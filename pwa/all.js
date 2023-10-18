/*
 * Assumes you are running a dev site locally on port 3000, and you can visit
 * different cobrands at FOO.localhost:3000. Assumes you have all cobrands
 * listed in your ALLOWED_COBRANDS. Given that, will create a batch of
 * screenshots in --outdir (or testing/ by default). Pass --type desktop or
 * --type mobile, and pass --path PATH to fetch a non-front page.
 */

const puppeteer = require('puppeteer');
const { type, path, outdir } = require('minimist')(process.argv.slice(2));

const TYPE = type || 'desktop';
const PATH = path || '';
const OUTDIR = outdir || 'testing';

const wait = (ms) => new Promise(res => setTimeout(res, ms));

async function visit_url(page, url, outparts) {
    await page.goto(url);
    await page.evaluate("document.querySelectorAll('.cookie-warning, .emergency-message, .site-message, .dev-site-notice').forEach(d => { d.style.display = 'none'; });");
    await page.screenshot({ path: OUTDIR + '/' + outparts.join('-') + '.png' });
}

async function visit(page, cobrand, live_domain) {
    console.log('  Processing', cobrand);
    var dev_url ='http://' + cobrand + '.localhost:3000/' + PATH;
    await visit_url(page, dev_url, [TYPE, cobrand, 'dev']);
    await visit_url(page, live_domain + PATH, [TYPE, cobrand, 'live']);
}

const COBRANDS = {
  'bathnes': 'https://fix.bathnes.gov.uk/',
  'bexley': 'https://fix.bexley.gov.uk/',
  'brent': 'https://report.brent.gov.uk/',
  'bristol': 'https://fixmystreet.bristol.gov.uk/',
  'bromley': 'https://fix.bromley.gov.uk/',
  'buckinghamshire': 'https://fixmystreet.buckinghamshire.gov.uk/',
  'camden': 'https://fixmystreet.camden.gov.uk/',
  'centralbedfordshire': 'https://fixmystreet.centralbedfordshire.gov.uk/',
  'cheshireeast': 'https://fixmystreet.cheshireeast.gov.uk/',
  'default': 'https://www.fixmystreet.com/',
  'fiksgatami': 'https://www.fiksgatami.no/',
  'fixamingata': 'https://www.fixamingata.se/',
  'fixmystreet': 'https://www.fixmystreet.com/',
  'gloucestershire': 'https://fixmystreet.gloucestershire.gov.uk/',
  'greenwich': 'https://fix.royalgreenwich.gov.uk/',
  'hackney': 'https://reportaproblem.hackney.gov.uk/',
  'hart': 'https://hart.fixmystreet.com/',
  'highwaysengland': 'https://report.nationalhighways.co.uk/',
  'hounslow': 'https://fms.hounslowhighways.org/',
  'isleofwight': 'https://fms.islandroads.com/',
  'kingston': 'https://waste-services.kingston.gov.uk/',
  'lincolnshire': 'https://fixmystreet.lincolnshire.gov.uk/',
  'merton': 'https://fixmystreet.merton.gov.uk/',
  'northamptonshire': 'https://fixmystreet.northamptonshire.gov.uk/',
  'northumberland': 'https://fix.northumberland.gov.uk/',
  'oxfordshire': 'https://fixmystreet.oxfordshire.gov.uk/',
  'peterborough': 'https://report.peterborough.gov.uk/',
  'rutland': 'https://rutland.fixmystreet.com/',
  'shropshire': 'https://improvingyourroads.shropshire.gov.uk/',
  'southwark': 'https://report.southwark.gov.uk/',
  'sutton': 'https://waste-services.sutton.gov.uk/',
  'tfl': 'https://streetcare.tfl.gov.uk/',
  'thamesmead': 'https://fix.thamesmeadnow.org.uk/',
  'westminster': 'https://report.westminster.gov.uk/',
  'zurich': 'https://www.zueriwieneu.ch/',
};

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  // Otherwise half of them are cookie banners
  page.setJavaScriptEnabled(false)

  if (TYPE == 'mobile') {
    await page.setViewport({ width: 375, height: 812, deviceScaleFactor: 3 });
  } else if (TYPE == 'desktop') {
    await page.setViewport({ width: 1200, height: 900, deviceScaleFactor: 1 });
  }

  for (const [cobrand, live_domain] of Object.entries(COBRANDS)) {
      await visit(page, cobrand, live_domain);
  }

  await browser.close();
})();
