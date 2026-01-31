import { MyDatabaseHelper } from '../helpers/MyDatabaseHelper';
import { MyDefineHook } from '../helpers/MyDefineHook';
import { ItemsServiceHelper } from '../helpers/ItemsServiceHelper';
import { TelegramHelper } from '../helpers/telegram/TelegramHelper';

const HOOK_NAME = 'plant-moisture-hook';

type SensorMeasurement = {
  id?: string | number;
  plant?: string | { id?: string | number } | null;
  moisture_percentage?: number | null;
};

type Plant = {
  id?: string | number;
  name?: string | null;
  moisture_percentage_dry?: number | null;
  moisture_percentage_tolerance?: number | null;
};

const SENSOR_MEASUREMENTS_COLLECTION = 'sensor_measurements';
const PLANTS_COLLECTION = 'plants';

export default MyDefineHook.defineHookWithAllTablesExisting(HOOK_NAME, async ({ action }, apiContext) => {
  action(SENSOR_MEASUREMENTS_COLLECTION + '.items.create', async ({ key, payload }, eventContext) => {
    if (!key && !payload) {
      return;
    }

    const myDatabaseHelper = new MyDatabaseHelper(apiContext, eventContext);
    const appSettings = await myDatabaseHelper.getAppSettingsHelper().getAppSettings();
    const botToken = appSettings?.telegram_bot_token;

    if (!botToken) {
      console.warn('Plant moisture hook skipped: missing telegram_bot_token in app settings.');
      return;
    }

    const measurementService = new ItemsServiceHelper<SensorMeasurement>(myDatabaseHelper, SENSOR_MEASUREMENTS_COLLECTION);
    let measurement = payload as Partial<SensorMeasurement> | undefined;

    if (key) {
      try {
        measurement = await measurementService.readOne(key);
      } catch (error) {
        console.warn('Plant moisture hook: failed to load created measurement, falling back to payload.', error);
      }
    }

    if (!measurement) {
      return;
    }

    const moistureValue = measurement.moisture_percentage;
    if (moistureValue === null || moistureValue === undefined || Number.isNaN(moistureValue)) {
      return;
    }

    const plantId = ItemsServiceHelper.getPrimaryKeyFromItemOrString(measurement.plant ?? undefined);
    if (!plantId) {
      console.warn('Plant moisture hook skipped: missing plant reference on measurement.');
      return;
    }

    const plantService = new ItemsServiceHelper<Plant>(myDatabaseHelper, PLANTS_COLLECTION);
    let plant: Plant | undefined;
    try {
      plant = await plantService.readOne(plantId, {
        fields: ['id', 'name', 'moisture_percentage_dry', 'moisture_percentage_tolerance'],
      });
    } catch (error) {
      console.warn(`Plant moisture hook skipped: plant ${plantId} not found.`, error);
      return;
    }

    const basePercentage = plant.moisture_percentage_dry;
    if (basePercentage === null || basePercentage === undefined || Number.isNaN(basePercentage)) {
      return;
    }

    const tolerance = plant.moisture_percentage_tolerance ?? 0;
    const threshold = basePercentage - tolerance;

    if (moistureValue >= threshold) {
      return;
    }

    const chatIds = Array.from(await TelegramHelper.getRecentChatIds(botToken));
    if (chatIds.length === 0) {
      console.warn('Plant moisture hook skipped: no recent Telegram chats found.');
      return;
    }

    const plantName = plant.name ?? `Pflanze ${plantId}`;
    const moistureText = moistureValue.toFixed(2);
    const thresholdText = threshold.toFixed(2);
    const toleranceText = tolerance.toFixed(2);
    const baseText = basePercentage.toFixed(2);
    const message = `🚨 ${plantName} ist zu trocken.\nMessung: ${moistureText}% (Schwelle ${baseText}% - Toleranz ${toleranceText}% = ${thresholdText}%).`;

    try {
      await TelegramHelper.sendSafeMessage(botToken, {
        chat_ids: chatIds,
        text: message,
      });
    } catch (error) {
      console.error('Plant moisture hook failed to send Telegram message.', error);
    }
  });
});
