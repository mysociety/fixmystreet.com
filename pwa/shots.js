const util = require('util');
const exec = util.promisify(require("child_process").exec);
const puppeteer = require('puppeteer');
const { cobrand, domain, theme } = require('minimist')(process.argv.slice(2));

if (!cobrand || !domain || !theme) {
    console.log('shots.js --cobrand [COBRAND] --domain [DOMAIN] --theme [THEME COLOUR]');
    process.exit(1);
}

async function visit(page, cobrand, url, scrshot) {
    console.log('  Processing', cobrand);
    await page.goto('https://' + url);
    // One non-JS cookie banner, don't want temporary messages
    await page.evaluate("document.querySelectorAll('.cookie-warning, .emergency-message').forEach(d => { d.style.display = 'none'; });");
    await page.screenshot({ path: scrshot });
}

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  // Otherwise half of them are cookie banners
  page.setJavaScriptEnabled(false)

  // frameit requires pictures in their own directory
  await exec('mkdir -p shots-i shots-a large small');

  console.log('iOS - iPhone X');
  await page.setViewport({ width: 375, height: 812, deviceScaleFactor: 3 });
  await visit(page, cobrand, domain, 'scrshot.png');
  // Pad for the notch
  await exec('convert -size 1125x132 xc:' + theme + ' pad.png');
  await exec('convert pad.png scrshot.png -append -gravity South -chop 0x132 shots-i/iphone-' + cobrand + '.png');

  console.log('Android - Google Pixel 4');
  await page.setViewport({ width: 393, height: 830, deviceScaleFactor: 2.75 });
  await visit(page, cobrand, domain, 'shots-a/android-' + cobrand + '.png');

  await browser.close();

  console.log('Framing - iPhone');
  await exec("fastlane run frameit force_device_type:'iPhone X' path:shots-i");
  console.log('Framing - Android');
  await exec("fastlane run frameit force_device_type:'Google Pixel 4' path:shots-a");
  console.log('Resizing');
  await exec('cp shots-a/*framed* shots-i/*framed* large/');
  await exec('mv shots-a/*framed* shots-i/*framed* small/');
  await exec('mogrify -resize 50% large/*');
  await exec('mogrify -resize 25% small/*');

  await exec('rm -rf shots-i shots-a');
})();
