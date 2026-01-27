import { makeTgBotClient } from '@effect-ak/tg-bot-client';

export type TelegramSendMessagePayload = {
  chat_id: string | number;
  text: string;
  parse_mode?: string;
  disable_notification?: boolean;
  message_thread_id?: number;
};

export class TelegramHelper {
  static async sendMessage(botToken: string, payload: TelegramSendMessagePayload) {
    const client = makeTgBotClient({ bot_token: botToken });
    await client.execute('sendMessage', {
      chat_id: payload.chat_id,
      text: payload.text,
      parse_mode: payload.parse_mode,
      disable_notification: payload.disable_notification,
      message_thread_id: payload.message_thread_id,
    });
  }
}
