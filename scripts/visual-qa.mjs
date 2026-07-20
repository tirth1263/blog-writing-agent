import { chromium } from "playwright-core";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const browserPath = process.env.BROWSER_PATH || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const output = path.resolve("artifacts");
await mkdir(output, { recursive: true });

const browser = await chromium.launch({ executablePath: browserPath, headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });

await page.goto("http://127.0.0.1:8765/", { waitUntil: "networkidle" });
await page.screenshot({ path: path.join(output, "showcase.png"), fullPage: true });

await page.getByRole("button", { name: /try a sample article/i }).click();
await page.locator("#profile").waitFor({ state: "visible", timeout: 10000 });
await page.locator("#topic").fill("How ethical AI can improve patient care without losing human trust");
await page.getByRole("button", { name: /generate in my voice/i }).click();
await page.locator("#draft").waitFor();
await page.screenshot({ path: path.join(output, "showcase-generated.png"), fullPage: true });

const streamlit = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
await streamlit.goto("http://127.0.0.1:8501/", { waitUntil: "domcontentloaded", timeout: 30000 });
await streamlit.getByText("Turn your writing into an").waitFor({ timeout: 30000 });
await streamlit.screenshot({ path: path.join(output, "streamlit.png"), fullPage: true });

console.log(JSON.stringify({
  showcaseTitle: await page.title(),
  generatedHeading: await page.locator("#articleContent h1").innerText(),
  showcaseOverflow: await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth),
  streamlitTitle: await streamlit.title(),
}, null, 2));

await browser.close();
