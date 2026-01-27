export interface ImageRawGeneratorInterface {

  generateImage(prompt: string): Promise<Buffer<ArrayBuffer>>;

}
