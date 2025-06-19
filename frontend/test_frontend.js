const puppeteer = require('puppeteer');

describe('Pong Frontend', () => {
  let browser, page;
  beforeAll(async () => {
    browser = await puppeteer.launch();
    page = await browser.newPage();
    await page.goto('http://localhost:8080');
  });
  afterAll(async () => {
    await browser.close();
  });

  it('loads the game UI', async () => {
    await page.waitForSelector('#pong-canvas');
    const title = await page.title();
    expect(title).toBe('Pong Game');
  });

  it('starts a game and displays scoreboard', async () => {
    await page.waitForSelector('#scoreboard');
    const text = await page.$eval('#scoreboard', el => el.textContent);
    expect(text).toMatch(/Player: \d+  \|  Computer: \d+/);
  });

  it('shows high scores', async () => {
    await page.waitForSelector('#highscores');
    const html = await page.$eval('#highscores', el => el.innerHTML);
    expect(html).toMatch(/High Scores/);
  });
}); 