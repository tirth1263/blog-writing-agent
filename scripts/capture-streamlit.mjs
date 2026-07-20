import { chromium } from "playwright-core";
import { mkdir } from "node:fs/promises";
import path from "node:path";

await mkdir(path.resolve("artifacts"), { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.BROWSER_PATH || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  headless: true,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
await page.goto("http://127.0.0.1:8501/", { waitUntil: "domcontentloaded", timeout: 30000 });
await page.getByText("Turn your writing into an").waitFor({ timeout: 30000 });
await page.screenshot({ path: path.resolve("artifacts/streamlit.png"), fullPage: true });
console.log(JSON.stringify({ title: await page.title(), bodyText: (await page.locator("body").innerText()).length }));
await browser.close();
