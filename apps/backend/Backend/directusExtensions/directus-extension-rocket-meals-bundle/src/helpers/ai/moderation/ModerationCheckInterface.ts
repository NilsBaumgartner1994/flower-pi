export type ModerationCheckResult = {
    flagged: boolean // whether the content is flagged by the model. This is required.
    categories?: Partial<{
        "sexual": boolean | null
        "sexual/minors": boolean | null
        "harassment": boolean | null
        "harassment/threatening": boolean | null
        "hate": boolean | null
        "hate/threatening": boolean | null
        "illicit": boolean | null
        "illicit/violent": boolean | null
        "self-harm": boolean | null
        "self-harm/intent": boolean | null
        "self-harm/instructions": boolean | null
        "violence": boolean | null
        "violence/graphic": boolean | null
    }>
    category_scores?: Partial<{
        "sexual": number
        "sexual/minors": number
        "harassment": number
        "harassment/threatening": number
        "hate": number
        "hate/threatening": number
        "illicit": number
        "illicit/violent": number
        "self-harm": number
        "self-harm/intent": number
        "self-harm/instructions": number
        "violence": number
        "violence/graphic": number
    }>
}

export class ModerationCheckResultHelper {
    public static createEmptyModerationCheckResult(): ModerationCheckResult {
        return {
            flagged: false,
        }
    }
}

export interface ModerationCheckInterface {

    checkTextModeration(text: string): Promise<ModerationCheckResult>;

}
