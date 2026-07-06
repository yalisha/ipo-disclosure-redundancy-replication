import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const project = "/Users/mac/computerscience/文章复现/IPO 信息披露冗余";
const runDir = path.join(project, "results/descriptive_stats_management_world_20260706");
const jsonPath = path.join(runDir, "management_world_descriptive_comparison_20260706.json");
const xlsxPath = path.join(runDir, "management_world_descriptive_comparison_20260706.xlsx");
const previewPath = path.join(runDir, "management_world_descriptive_comparison_20260706.png");

function fmtNum(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return null;
  return Number(value);
}

function rowFor(item) {
  return [
    item.variable,
    item.label,
    fmtNum(item.current_N),
    fmtNum(item.current_mean),
    fmtNum(item.current_std),
    fmtNum(item.current_p25),
    fmtNum(item.current_median),
    fmtNum(item.current_p75),
    fmtNum(item.original_N),
    fmtNum(item.original_mean),
    fmtNum(item.original_median),
    fmtNum(item.mean_diff),
  ];
}

const data = JSON.parse(await fs.readFile(jsonPath, "utf8"));
const panels = ["Panel A 因变量", "Panel B 核心自变量", "Panel C 控制变量"];
const header = ["变量", "变量含义", "N", "均值", "标准差", "P25", "中位数", "P75", "原文N", "原文均值", "原文中位数", "均值差"];

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("描述性统计");
sheet.showGridLines = false;

sheet.getRange("A1:L1").merge();
sheet.getRange("A1:L1").values = [["表1  主要变量描述性统计对比"]];
sheet.getRange("A1:L1").format.font = { bold: true, size: 14, name: "SimSun" };
sheet.getRange("A1:L1").format.horizontalAlignment = "center";

sheet.getRange("A2:L2").merge();
sheet.getRange("A2:L2").values = [[`样本：当前复现 543 家科创板 IPO；原文统计值：原文 Panel A/附录口径；生成日期：2026-07-06`]];
sheet.getRange("A2:L2").format.font = { italic: true, size: 10, name: "SimSun" };
sheet.getRange("A2:L2").format.horizontalAlignment = "left";

let row = 4;
sheet.getRange(`A${row}:L${row}`).values = [header];
sheet.getRange(`A${row}:L${row}`).format.font = { bold: true, name: "SimSun" };
sheet.getRange(`A${row}:L${row}`).format.borders = {
  top: { style: "medium", color: "#000000" },
  bottom: { style: "thin", color: "#000000" },
};
sheet.getRange(`A${row}:L${row}`).format.horizontalAlignment = "center";
row += 1;

for (const panel of panels) {
  sheet.getRange(`A${row}:L${row}`).merge();
  sheet.getRange(`A${row}:L${row}`).values = [[panel]];
  sheet.getRange(`A${row}:L${row}`).format.font = { bold: true, name: "SimSun" };
  sheet.getRange(`A${row}:L${row}`).format.fill = { color: "#F2F2F2" };
  sheet.getRange(`A${row}:L${row}`).format.borders = {
    top: { style: "thin", color: "#808080" },
    bottom: { style: "thin", color: "#808080" },
  };
  row += 1;
  const items = data.filter((d) => d.panel === panel);
  const values = items.map(rowFor);
  sheet.getRangeByIndexes(row - 1, 0, values.length, header.length).values = values;
  sheet.getRangeByIndexes(row - 1, 0, values.length, 2).format.horizontalAlignment = "left";
  sheet.getRangeByIndexes(row - 1, 2, values.length, header.length - 2).format.horizontalAlignment = "right";
  sheet.getRangeByIndexes(row - 1, 2, values.length, header.length - 2).setNumberFormat("0.000");
  sheet.getRangeByIndexes(row - 1, 2, values.length, 1).setNumberFormat("0");
  sheet.getRangeByIndexes(row - 1, 8, values.length, 1).setNumberFormat("0");
  row += values.length;
}

sheet.getRange(`A${row}:L${row}`).format.borders = {
  top: { style: "medium", color: "#000000" },
};
row += 1;
sheet.getRange(`A${row}:L${row + 2}`).merge(true);
sheet.getRange(`A${row}:L${row + 2}`).values = [[
  "注：本表报告当前复现样本与原文样本的描述性统计。NumIndSeg 与 NumProdSeg 为上市当年 FN_Fn048 年报附注替代口径，主营业务收入分部优先，缺失时以营业收入分部补缺，并取 ln(1+count)；RD_Staff 使用 IPO 来源优先的 PT_LCRDSPENDING 上市前一年口径。均值差为当前均值减原文均值。"
], [null], [null]];
sheet.getRange(`A${row}:L${row + 2}`).format.font = { size: 10, name: "SimSun" };
sheet.getRange(`A${row}:L${row + 2}`).format.wrapText = true;
sheet.getRange(`A${row}:L${row + 2}`).format.verticalAlignment = "top";

const widths = [15, 18, 8, 10, 10, 10, 10, 10, 9, 11, 12, 10];
for (let c = 0; c < widths.length; c += 1) {
  sheet.getRangeByIndexes(0, c, row + 3, 1).format.columnWidth = widths[c];
}
sheet.getRangeByIndexes(0, 0, row + 3, header.length).format.font = { name: "SimSun" };
sheet.freezePanes.freezeRows(4);

const noteSheet = workbook.worksheets.add("变量口径");
noteSheet.showGridLines = false;
noteSheet.getRange("A1:D1").values = [["变量", "变量含义", "类别", "当前口径说明"]];
noteSheet.getRange("A1:D1").format.font = { bold: true, name: "SimSun" };
noteSheet.getRange("A1:D1").format.fill = { color: "#F2F2F2" };
noteSheet.getRange("A1:D1").format.borders = { bottom: { style: "thin", color: "#000000" } };
const noteRows = data.map((d) => [d.variable, d.label, d.panel, d.note]);
noteSheet.getRangeByIndexes(1, 0, noteRows.length, 4).values = noteRows;
noteSheet.getRangeByIndexes(0, 0, noteRows.length + 1, 4).format.font = { name: "SimSun" };
noteSheet.getRangeByIndexes(0, 0, noteRows.length + 1, 1).format.columnWidth = 16;
noteSheet.getRangeByIndexes(0, 1, noteRows.length + 1, 1).format.columnWidth = 18;
noteSheet.getRangeByIndexes(0, 2, noteRows.length + 1, 1).format.columnWidth = 18;
noteSheet.getRangeByIndexes(0, 3, noteRows.length + 1, 1).format.columnWidth = 78;
noteSheet.getRangeByIndexes(1, 3, noteRows.length, 1).format.wrapText = true;
noteSheet.freezePanes.freezeRows(1);

const inspect = await workbook.inspect({
  kind: "table",
  sheetId: "描述性统计",
  range: "A1:L28",
  include: "values,formulas",
  tableMaxRows: 28,
  tableMaxCols: 12,
});
console.log(inspect.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

const preview = await workbook.render({ sheetName: "描述性统计", range: "A1:L29", scale: 1, format: "png" });
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

await fs.mkdir(runDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(xlsxPath);
console.log(`xlsx=${xlsxPath}`);
console.log(`preview=${previewPath}`);
