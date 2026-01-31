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
  moisture_percentage_current?: number | null;
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

    const plantService = new ItemsServiceHelper<Plant>(myDatabaseHelper, PLANTS_COLLECTION);
    let plant: Plant | undefined;
    try {
      const plants = await plantService.findItems(
        {},
        {
          limit: 1,
          fields: [
            'id',
            'name',
            'moisture_percentage_dry',
            'moisture_percentage_current',
            'moisture_percentage_tolerance',
          ],
        }
      );
      plant = plants[0];
    } catch (error) {
      console.warn('Plant moisture hook skipped: failed to load first plant.', error);
      return;
    }

    if (!plant) {
      console.warn('Plant moisture hook skipped: no plant found.');
      return;
    }

    const basePercentage = plant.moisture_percentage_dry;
    const toleranceValue = plant.moisture_percentage_tolerance;
    const hasBase = basePercentage !== null && basePercentage !== undefined && !Number.isNaN(basePercentage);
    const hasTolerance = toleranceValue !== null && toleranceValue !== undefined && !Number.isNaN(toleranceValue);

    if (!hasBase && !hasTolerance) {
      return;
    }

    const normalizedBase = hasBase ? basePercentage : 0;
    const tolerance = hasTolerance ? toleranceValue : 0;
    const threshold = normalizedBase - tolerance;

    const plantId = plant.id;
    if (!plantId) {
      return;
    }

    try {
      await plantService.updateOne(plantId, { moisture_percentage_current: moistureValue });
    } catch (error) {
      console.warn(`Plant moisture hook: failed to update moisture current for plant ${plantId}.`, error);
    }

    if (moistureValue >= threshold) {
      return;
    }

    const previousMoisture = plant.moisture_percentage_current;
    const wasBelowThreshold =
      previousMoisture !== null &&
      previousMoisture !== undefined &&
      !Number.isNaN(previousMoisture) &&
      previousMoisture < threshold;
    if (wasBelowThreshold) {
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
    const baseText = normalizedBase.toFixed(2);
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
