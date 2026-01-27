import {ImageGeneratorProps, ImageSafeGenerator} from "./ImageSafeGenerator";

export class ImageSafeGeneratorFood extends ImageSafeGenerator{

  constructor(props: ImageGeneratorProps) {
    super(props);
  }

  public async generateImage(food_description: string): Promise<Buffer<ArrayBuffer>> {
    let prompt = "A realistic photo of a typical cafeteria meal on a white plate, photographed on a neutral background, natural lighting, soft shadows, slightly imperfect food presentation, realistic textures, natural portion sizes, minimal reflections, focus on the main dish, shallow depth of field, realistic colors, not overly vibrant, no artistic styling, no stock photo look. The meal is: " + food_description
    return super.generateImage(prompt);
  }

}
