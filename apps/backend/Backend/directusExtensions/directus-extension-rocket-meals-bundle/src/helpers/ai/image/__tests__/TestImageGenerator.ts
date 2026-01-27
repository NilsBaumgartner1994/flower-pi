// small jest test
import {describe, expect, it} from '@jest/globals';
import {ImageRawGeneratorInterface} from "../ImageRawGenerator";
import fs from "fs/promises";
import {ImageRawGeneratorChatGpt} from "../ImageRawGeneratorChatGpt";
import {ModerationCheckChatGpt} from "../../moderation/ModerationCheckChatGpt";
import {ModerationCheckMock} from "../../moderation/ModerationCheckMock";
import {ImageRawGeneratorMock} from "../ImageRawGeneratorMock";
import {ModerationCheckInterface} from "../../moderation/ModerationCheckInterface";
import {ImageSafeGeneratorFood} from "../ImageSafeGeneratorFood";

const SECONDS = 1000;

describe('Image Generation Tests', () => {
  // should find atleast one meal offer
  it('Food Image Generation', async () => {
    let apiKey = ""

    let moderationCheck: ModerationCheckInterface = new ModerationCheckMock();
    let imageRawGenerator: ImageRawGeneratorInterface = new ImageRawGeneratorMock();

    if(apiKey && apiKey.length > 0) {
      let baseProps = {
        apiKey: apiKey,
      }

      moderationCheck = new ModerationCheckChatGpt(baseProps);
      imageRawGenerator = new ImageRawGeneratorChatGpt(baseProps);
    }

    let safeImageGenerator = new ImageSafeGeneratorFood({
        moderationCheck: moderationCheck,
        imageGenerator: imageRawGenerator,
    })

    let testOutputFilePath = "/Users/nilsbaumgartner/Desktop/test_food_image_generation.png";
    let testPrompt = "Hähnchenkeule, Schaschliksauce, Bio-Maisgemüse, Bunte Bio-Spirelli, Banane";

    //console.log("Starting food image generation test...");
    let startTime = Date.now();
    let image_bytes = await safeImageGenerator.generateImage(testPrompt);

    expect(image_bytes.length).toBeGreaterThan(0);
    let endTime = Date.now();
    let durationSeconds = (endTime - startTime) / 1000;
    
    //console.log(`Food image generation test completed in ${durationSeconds.toFixed(2)} seconds. Image saved to ${testOutputFilePath}`);

    //await fs.writeFile(testOutputFilePath, image_bytes);


  }, 180 * SECONDS);

});
