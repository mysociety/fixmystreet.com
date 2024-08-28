const puppeteer = require('puppeteer');
const { base, path, width, height } = require('minimist')(process.argv.slice(2));

if (!base || !path) {
    console.log('check.js --base [http://{s}.localhost:3000] --path [/faq] [--width N] [--height N]');
    process.exit(1);
}

const SITES = [
    'bathnes', 'bexley', 'borsetshire', 'brent', 'bristol', 'bromley',
    'buckinghamshire', 'camden', 'centralbedfordshire', 'cheshireeast',
    'cyclinguk', 'eastherts', 'gloucestershire', 'greenwich', 'hackney',
    'hart', 'highwaysengland', 'hounslow', 'isleofwight', 'kingston',
    'lincolnshire', 'merton', 'northnorthants', 'northumberland',
    'oxfordshire', 'peterborough', 'rutland', 'shropshire', 'southwark',
    'sutton', 'tfl', 'thamesmead', 'westminster', 'westnorthants',
    'fixmystreet',
];

async function visit(page, url, scrshot) {
    console.log('  Processing', url);
    await page.goto(url);
    await page.evaluate("document.querySelectorAll('.cookie-warning, .emergency-message, .site-message, .dev-site-notice').forEach(d => { d.style.display = 'none'; });");
    await page.screenshot({ path: scrshot });
}

(async () => {
  const browser = await puppeteer.launch({ ignoreHTTPSErrors: true });
  const page = await browser.newPage();

  // Otherwise half of them are cookie banners
  page.setJavaScriptEnabled(false);

  if (width && height) {
      await page.setViewport({ width: width, height: height });
  }

  for (cobrand of SITES) {
      await visit(page, base.replace('{s}', cobrand) + path, cobrand + '.png');
  }

  await browser.close();
})();
