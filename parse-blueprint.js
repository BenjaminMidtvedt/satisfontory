import * as fs from "fs";
import { Parser } from "@etothepii/satisfactory-file-parser";

// Read the blueprint files
const file = new Uint8Array(fs.readFileSync("C:/Users/GU/AppData/Local/FactoryGame/Saved/SaveGames/blueprints/TEST2/New Blueprint.sbp")).buffer;
const configFile = new Uint8Array(fs.readFileSync("C:/Users/GU/AppData/Local/FactoryGame/Saved/SaveGames/blueprints/TEST2/New Blueprint.sbpcfg"))
  .buffer;

// Parse the blueprint
const blueprint = Parser.ParseBlueprintFiles(
  "Framed Glass Container",
  file,
  configFile
);

// Write to JSON file
fs.writeFileSync("New Blueprint.json", JSON.stringify(blueprint, null, 2));

console.log("Blueprint parsed successfully!");
console.log("Output saved to: Framed Glass Container.json");
