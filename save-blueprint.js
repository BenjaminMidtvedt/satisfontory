import * as fs from "fs";
import { Parser } from "@etothepii/satisfactory-file-parser";

// Read the blueprint files
const file = fs.readFileSync("New Blueprint 2.json");
// Parse the blueprint
const blueprint = JSON.parse(file.toString());

let mainFileHeader;
const mainFileBodyChunks = [];
const summary = Parser.WriteBlueprintFiles(
  blueprint,
  (header) => {
    console.log("on main file header.");
    mainFileHeader = header;
  },
  (chunk) => {
    console.log("on main file body chunk.");
    mainFileBodyChunks.push(chunk);
  }
);

// Write to JSON file
const out_path =
  "C:/Users/GU/AppData/Local/FactoryGame/Saved/SaveGames/blueprints/TEST2/New Blueprint 2.sbp";
const out_path_cfg =
  "C:/Users/GU/AppData/Local/FactoryGame/Saved/SaveGames/blueprints/TEST2/New Blueprint 2.sbpcfg";
// write complete .sbp file back to disk
fs.writeFileSync(
  out_path,
  new Uint8Array(Buffer.concat([mainFileHeader, ...mainFileBodyChunks]))
);

// write .sbpcfg file back to disk, we get that data from the result of WriteBlueprintFiles
fs.writeFileSync(out_path_cfg, new Uint8Array(summary.configFileBinary));
