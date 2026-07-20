import { chromium } from "playwright-core";
import path from "node:path";
import { pathToFileURL } from "node:url";

const browser = await chromium.launch({
  executablePath: process.env.BROWSER_PATH || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  headless: true,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 920 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.resolve("docs/index.html")).href, { waitUntil: "domcontentloaded", timeout: 30000 });
await page.locator(".hero h1").waitFor({ timeout: 10000 });
await page.screenshot({ path: path.resolve("docs/preview.png") });
console.log(JSON.stringify({ title: await page.title(), width: await page.evaluate(() => document.body.scrollWidth) }));
await browser.close();
