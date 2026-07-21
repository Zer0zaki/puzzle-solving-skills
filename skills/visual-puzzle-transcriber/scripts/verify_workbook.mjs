import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

if (process.argv.length < 3) {
  throw new Error("usage: verify_workbook.mjs WORKBOOK_XLSX");
}

const workbookPath = process.argv[2];
const input = await FileBlob.load(workbookPath);
const wb = await SpreadsheetFile.importXlsx(input);
const gate = wb.worksheets.getItem("锁定门");
const cells = wb.worksheets.getItem("逐格转录");
const engines = wb.worksheets.getItem("OCR引擎");
const errors = await wb.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "reimported workbook formula error scan",
  maxChars: 8000,
});

console.log(JSON.stringify({
  gateValues: gate.getRange("A4:B14").values,
  gateFormulas: gate.getRange("B7:B14").formulas,
  firstCells: cells.getRange("A4:J8").values,
  engineRows: engines.getRange("A4:D8").values,
  formulaErrors: errors.ndjson,
}, null, 2));
