import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

if (process.argv.length < 4) {
  throw new Error("usage: build_transcription_workbook.mjs REPORT_JSON OUTPUT_XLSX");
}

const reportPath = path.resolve(process.argv[2]);
const outputPath = path.resolve(process.argv[3]);
const outputDir = path.dirname(outputPath);
const report = JSON.parse(await fs.readFile(reportPath, "utf8"));
await fs.mkdir(outputDir, { recursive: true });

const wb = Workbook.create();
const sheets = {
  gate: wb.worksheets.add("锁定门"),
  cells: wb.worksheets.add("逐格转录"),
  uncertain: wb.worksheets.add("不确定字符"),
  colors: wb.worksheets.add("颜色聚类"),
  geometry: wb.worksheets.add("线箭头交点"),
  diff: wb.worksheets.add("图片差分"),
  engines: wb.worksheets.add("OCR引擎"),
};

const palette = {
  navy: "#102A3A",
  blue: "#2B5F75",
  paleBlue: "#DCEAF0",
  cream: "#FFFDF7",
  paper: "#F4F0E8",
  ink: "#1D2930",
  muted: "#667780",
  line: "#D4D9D7",
  green: "#DDEDE5",
  greenText: "#176A52",
  amber: "#F6E7C6",
  amberText: "#8D5D10",
  red: "#F2DDDA",
  redText: "#963E38",
  white: "#FFFFFF",
};

function title(sheet, main, subtitle, endCol) {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${endCol}1`).merge();
  sheet.getRange("A1").values = [[main]];
  sheet.getRange(`A1:${endCol}1`).format = {
    fill: palette.navy,
    font: { bold: true, color: palette.white, size: 19 },
    verticalAlignment: "center",
  };
  sheet.getRange(`A1:${endCol}1`).format.rowHeight = 38;
  sheet.getRange(`A2:${endCol}2`).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A2:${endCol}2`).format = {
    fill: palette.paleBlue,
    font: { color: palette.navy, italic: true, size: 10 },
    wrapText: true,
    verticalAlignment: "center",
  };
  sheet.getRange(`A2:${endCol}2`).format.rowHeight = 30;
}

function header(sheet, range) {
  sheet.getRange(range).format = {
    fill: palette.blue,
    font: { bold: true, color: palette.white },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "inside", style: "thin", color: "#7995A3" },
  };
  sheet.getRange(range).format.rowHeight = 30;
}

function body(sheet, range) {
  sheet.getRange(range).format = {
    fill: palette.cream,
    font: { color: palette.ink, size: 10 },
    wrapText: true,
    verticalAlignment: "top",
    borders: { preset: "inside", style: "thin", color: palette.line },
  };
}

function addTable(sheet, range, name) {
  const table = sheet.tables.add(range, true, name);
  table.style = "TableStyleMedium2";
  table.showFilterButton = true;
  table.showBandedRows = true;
  return table;
}

function setWidths(sheet, widths, rowCount) {
  widths.forEach((width, index) => {
    sheet.getRangeByIndexes(0, index, rowCount, 1).format.columnWidth = width;
  });
}

function cfText(range, text, fill, fontColor) {
  range.conditionalFormats.add("containsText", {
    text,
    format: { fill, font: { color: fontColor, bold: true } },
  });
}

function stringify(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

const gate = sheets.gate;
title(gate, "视觉转录锁定门", "只有覆盖率、图像清单、未跟踪区域、OCR证据与人工复核全部通过，才允许把规律称为“锁定”。", "F");
gate.getRange("A4:B4").values = [["门槛项目", "当前值"]];
header(gate, "A4:B4");
gate.getRange("A5:A14").values = [
  ["覆盖率阈值"],
  ["预计区域数"],
  ["已覆盖区域数"],
  ["当前覆盖率"],
  ["图像清单已确认"],
  ["未跟踪区域"],
  ["成功OCR引擎数"],
  ["存在文字材料"],
  ["人工复核"],
  ["锁定许可"],
];
body(gate, "A5:B14");
gate.getRange("B5").values = [[Number(report.gate.coverage_threshold ?? 0.95)]];
gate.getRange("B6").values = [[Number(report.gate.expected_regions ?? report.cells.length)]];
gate.getRange("B7").values = [[Number(report.gate.covered_regions ?? 0)]];
gate.getRange("B8").values = [[Number(report.gate.coverage ?? 0)]];
gate.getRange("B9").values = [[report.gate.inventory_verified ? "是" : "否"]];
gate.getRange("B10").values = [[Number(report.gate.untracked_regions ?? 0)]];
gate.getRange("B11").values = [[Number(report.gate.successful_ocr_engines?.length ?? 0)]];
gate.getRange("B12").values = [[report.gate.text_present ? "是" : "否"]];
gate.getRange("B13").values = [[report.gate.review_manifest_valid ? "已导入" : "待导入"]];
gate.getRange("B14").values = [[report.gate.permission || "禁止"]];
gate.getRange("B5:B8").format.numberFormat = "0.0%";
gate.getRange("B6:B7").format.numberFormat = "0";
gate.getRange("B10:B11").format.numberFormat = "0";
cfText(gate.getRange("B14"), "允许", palette.green, palette.greenText);
cfText(gate.getRange("B14"), "禁止", palette.red, palette.redText);
gate.getRange("D4:F4").merge();
gate.getRange("D4").values = [["当前阻断原因"]];
header(gate, "D4:F4");
const reasons = report.gate.blocking_reasons?.length ? report.gate.blocking_reasons : ["无自动阻断；仍须完成机制独立验证。"];
gate.getRange(`D5:F${4 + reasons.length}`).merge(true);
gate.getRange(`D5:D${4 + reasons.length}`).values = reasons.map((reason) => [reason]);
body(gate, `D5:F${4 + reasons.length}`);
gate.getRange(`D5:F${4 + reasons.length}`).format.rowHeight = 28;
gate.getRange("A16:F16").merge();
gate.getRange("A16").values = [["纪律：锁定门显示“禁止”时，局部规律只能标记为“候选”或“阶段结论”。"]];
gate.getRange("A16:F16").format = { fill: palette.red, font: { bold: true, color: palette.redText }, wrapText: true };
gate.getRange("A16:F16").format.rowHeight = 32;
setWidths(gate, [28, 18, 4, 28, 28, 28], 30);
gate.freezePanes.freezeRows(4);

const cells = sheets.cells;
title(cells, "逐格转录", "一格一行；自动观察、OCR原文、人工裁定与有效转录分列保存。审核请修改 inventory_review_template.json 后重新运行。", "U");
const cellHeaders = ["区域ID", "行", "列", "像素坐标", "裁剪图", "转录状态", "自动状态", "OCR融合原文", "人工裁定", "有效转录", "OCR状态", "OCR置信度", "各引擎候选", "主色", "颜色簇", "线段", "箭头", "交点", "总体置信度", "复核说明", "用户确认"];
cells.getRange("A4:U4").values = [cellHeaders];
header(cells, "A4:U4");
const cellRows = report.cells.length ? report.cells.map((cell) => [
  cell.region_id, cell.row, cell.col, stringify(cell.bbox), cell.crop, cell.transcription_status,
  cell.auto_transcription_status, cell.text, cell.reviewed_text, cell.effective_text, cell.ocr_status,
  Number(cell.ocr_confidence || 0), stringify(cell.ocr_candidates), cell.dominant_color, stringify(cell.color_clusters),
  stringify(cell.line_ids), stringify(cell.arrow_ids), stringify(cell.intersection_ids), cell.confidence,
  cell.review_note, cell.user_confirmed || "待确认",
]) : [["", "", "", "", "", "未处理", "", "", "", "", "", 0, "", "", "", "", "", "", "低", "", "待确认"]];
const cellEnd = 4 + cellRows.length;
cells.getRange(`A5:U${cellEnd}`).values = cellRows;
body(cells, `A5:U${cellEnd}`);
cells.getRange(`F5:F${cellEnd}`).dataValidation = { rule: { type: "list", values: ["未处理", "不确定", "已转录"] } };
cells.getRange(`S5:S${cellEnd}`).dataValidation = { rule: { type: "list", values: ["低", "中", "高", "锁定"] } };
cells.getRange(`U5:U${cellEnd}`).dataValidation = { rule: { type: "list", values: ["待确认", "是", "否"] } };
cells.getRange(`L5:L${cellEnd}`).format.numberFormat = "0.0%";
cfText(cells.getRange(`F5:F${cellEnd}`), "已转录", palette.green, palette.greenText);
cfText(cells.getRange(`F5:F${cellEnd}`), "不确定", palette.amber, palette.amberText);
cfText(cells.getRange(`F5:F${cellEnd}`), "未处理", palette.red, palette.redText);
addTable(cells, `A4:U${cellEnd}`, "CellTranscriptionTable");
setWidths(cells, [14, 7, 7, 21, 34, 14, 14, 22, 22, 22, 14, 14, 42, 12, 36, 18, 18, 18, 14, 34, 14], cellEnd);
cells.getRange(`A5:U${cellEnd}`).format.rowHeight = 38;
cells.freezePanes.freezeRows(4);
cells.freezePanes.freezeColumns(3);

const uncertain = sheets.uncertain;
title(uncertain, "不确定字符", "这里只收集需要人工复核的读法；填写“用户裁定”时保留原始候选。", "G");
const uncertainHeaders = ["区域ID", "像素坐标", "当前最佳读法", "各引擎候选", "不确定原因", "裁剪图", "用户裁定"];
uncertain.getRange("A4:G4").values = [uncertainHeaders];
header(uncertain, "A4:G4");
const uncertainRows = report.uncertain.length ? report.uncertain.map((item) => [item.region_id, stringify(item.bbox), item.best_reading, stringify(item.candidates), item.reason, item.crop, item.user_resolution || ""]) : [["", "", "", "", "当前没有自动识别出的不确定项", "", ""]];
const uncertainEnd = 4 + uncertainRows.length;
uncertain.getRange(`A5:G${uncertainEnd}`).values = uncertainRows;
body(uncertain, `A5:G${uncertainEnd}`);
addTable(uncertain, `A4:G${uncertainEnd}`, "UncertainCharacterTable");
setWidths(uncertain, [14, 22, 22, 48, 38, 38, 24], uncertainEnd);
uncertain.getRange(`A5:G${uncertainEnd}`).format.rowHeight = 42;
uncertain.freezePanes.freezeRows(4);

const colors = sheets.colors;
title(colors, "颜色取样与聚类", "每个区域按像素比例列出主要颜色；颜色名称和谜题含义需另行解释。", "E");
colors.getRange("A4:E4").values = [["区域ID", "颜色排名", "RGB", "Hex", "像素比例"]];
header(colors, "A4:E4");
const colorRows = report.colors.length ? report.colors.map((item) => [item.region_id, item.rank, stringify(item.rgb), item.hex, Number(item.proportion)]) : [["", "", "", "", 0]];
const colorEnd = 4 + colorRows.length;
colors.getRange(`A5:E${colorEnd}`).values = colorRows;
body(colors, `A5:E${colorEnd}`);
colors.getRange(`E5:E${colorEnd}`).format.numberFormat = "0.0%";
addTable(colors, `A4:E${colorEnd}`, "ColorClusterTable");
setWidths(colors, [16, 14, 22, 16, 16], colorEnd);
colors.freezePanes.freezeRows(4);

const geometry = sheets.geometry;
title(geometry, "线段、箭头、交点与方向", "自动识别结果均是观察候选；箭头使用线段端点＋多边形箭头头部启发式。", "H");
geometry.getRange("A4:H4").values = [["类型", "ID", "区域ID", "几何数据", "角度/方向", "长度", "关联对象", "识别方法"]];
header(geometry, "A4:H4");
const geometryRows = [];
for (const line of report.geometry.lines ?? []) geometryRows.push(["线段", line.id, line.region_id || "", stringify(line.points), line.angle, line.length, "", "HoughLinesP"]);
for (const arrow of report.geometry.arrows ?? []) geometryRows.push(["箭头", arrow.id, arrow.region_id || "", `${stringify(arrow.start)} → ${stringify(arrow.end)}`, arrow.direction_degrees, "", arrow.line_id, arrow.method]);
for (const intersection of report.geometry.intersections ?? []) geometryRows.push(["交点", intersection.id, intersection.region_id || "", `[${intersection.x},${intersection.y}]`, "", "", `${intersection.line_a}, ${intersection.line_b}`, "线段求交"]);
if (!geometryRows.length) geometryRows.push(["", "", "", "未检测到几何元素", "", "", "", ""]);
const geometryEnd = 4 + geometryRows.length;
geometry.getRange(`A5:H${geometryEnd}`).values = geometryRows;
body(geometry, `A5:H${geometryEnd}`);
addTable(geometry, `A4:H${geometryEnd}`, "GeometryEvidenceTable");
setWidths(geometry, [12, 12, 14, 36, 18, 14, 24, 30], geometryEnd);
geometry.freezePanes.freezeRows(4);

const diff = sheets.diff;
title(diff, "点击前后图片差分", `配准方式：${report.difference.alignment || "未提供后态图片"}。差分区域只表示像素发生变化，不自动解释原因。`, "F");
diff.getRange("A4:F4").values = [["变化ID", "区域ID", "像素坐标", "面积", "质心", "备注"]];
header(diff, "A4:F4");
const diffRows = report.difference.components?.length ? report.difference.components.map((item) => [item.id, item.region_id || "", stringify(item.bbox), item.area, stringify(item.centroid), "待解释"]): [["", "", "", "", "", report.difference.provided ? "没有超过阈值的变化区域" : "未提供后态图片"]];
const diffEnd = 4 + diffRows.length;
diff.getRange(`A5:F${diffEnd}`).values = diffRows;
body(diff, `A5:F${diffEnd}`);
addTable(diff, `A4:F${diffEnd}`, "ImageDifferenceTable");
setWidths(diff, [14, 14, 24, 14, 20, 34], diffEnd);
diff.freezePanes.freezeRows(4);

const engines = sheets.engines;
title(engines, "OCR引擎状态", "成功与失败必须同时保留；不得把“请求了多个引擎”写成“多个引擎成功”。", "D");
engines.getRange("A4:D4").values = [["引擎", "成功", "识别项数", "错误/说明"]];
header(engines, "A4:D4");
const engineRows = report.engines.length ? report.engines.map((item) => [item.engine, item.success ? "是" : "否", Number(item.items || 0), item.error || ""]) : [["", "否", 0, "没有OCR引擎记录"]];
const engineEnd = 4 + engineRows.length;
engines.getRange(`A5:D${engineEnd}`).values = engineRows;
body(engines, `A5:D${engineEnd}`);
cfText(engines.getRange(`B5:B${engineEnd}`), "是", palette.green, palette.greenText);
cfText(engines.getRange(`B5:B${engineEnd}`), "否", palette.red, palette.redText);
addTable(engines, `A4:D${engineEnd}`, "OcrEngineTable");
setWidths(engines, [24, 14, 16, 56], engineEnd);
engines.freezePanes.freezeRows(4);

const inspect = await wb.inspect({
  kind: "workbook,sheet,table",
  maxChars: 12000,
  tableMaxRows: 8,
  tableMaxCols: 12,
  tableMaxCellChars: 100,
});
await fs.writeFile(path.join(outputDir, "workbook_inspect.ndjson"), inspect.ndjson, "utf8");
const errors = await wb.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "visual transcription formula error scan",
});
await fs.writeFile(path.join(outputDir, "workbook_formula_errors.ndjson"), errors.ndjson, "utf8");

for (const [name, sheet] of Object.entries(sheets)) {
  const preview = await wb.render({ sheetName: sheet.name, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(outputDir, `preview_${name}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(outputPath);
console.log(JSON.stringify({ outputPath, sheets: Object.values(sheets).map((sheet) => sheet.name) }));
