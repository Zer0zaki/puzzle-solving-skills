#!/usr/bin/env node
import fs from "node:fs/promises";

const file = process.argv[2];
if (!file) {
  console.error("Usage: node validate_puzzle_packet.mjs <packet.md>");
  process.exit(2);
}

const required = [
  "题号/题名",
  "最终需要",
  "硬约束",
  "已确认正确的信息",
  "材料清单",
  "尚不确定的信息",
  "允许的工具和操作",
  "网络与比赛界面边界",
  "证明与时间策略",
  "答案格式",
];

const source = await fs.readFile(file, "utf8");
const sections = new Map();
const lines = source.split(/\r?\n/);
let current = null;
for (const line of lines) {
  const match = line.match(/^##\s+(.+?)\s*$/);
  if (match) {
    current = match[1].trim();
    sections.set(current, []);
  } else if (current) {
    sections.get(current).push(line);
  }
}

const results = required.map((name) => {
  const body = (sections.get(name) ?? []).join("\n").trim();
  return { name, present: sections.has(name), filled: body.length > 0, chars: body.length };
});

const blockingNames = new Set(["题号/题名", "最终需要", "硬约束", "材料清单", "网络与比赛界面边界", "答案格式"]);
const blocking = results.filter((item) => blockingNames.has(item.name) && !item.filled).map((item) => item.name);
const warnings = results.filter((item) => !blockingNames.has(item.name) && !item.filled).map((item) => item.name);

const output = { file, valid: blocking.length === 0, blocking, warnings, sections: results };
console.log(JSON.stringify(output, null, 2));
process.exit(output.valid ? 0 : 1);
