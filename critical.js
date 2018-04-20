var penthouse = require('penthouse');

penthouse({
    url: 'https://www.fixmystreet.com/',
    // cssString: 'body { color; red }', // the original css to extract critcial css from
    css: '/data/vhost/www.fixmystreet.com/fixmystreet/web/cobrands/fixmystreet.com/base.css',

    width: 480,
    height: 1000,
    keepLargerMediaQueries: false,
    forceInclude: [
      '#front-main a#geolocate_link',
      'svg|g.site-logo__svg',
    ],
    propertiesToRemove: [
    ],
    timeout: 30000,                 // ms; abort critical CSS generation after this timeout
    strict: true,                  // set to true to throw on CSS errors (will run faster if no errors)
    maxEmbeddedBase64Length: 1000,  // characters; strip out inline base64 encoded resources larger than this
    userAgent: 'Penthouse Critical Path CSS Generator', // specify which user agent string when loading the page
    renderWaitTime: 1000,            // ms; render wait timeout before CSS processing starts (default: 100)
    blockJSRequests: true,          // set to false to load (external) JS (default: true)
    //customPageHeaders: {
    //  'Accept-Encoding': 'identity' // add if getting compression errors like 'Data corrupted'
    //},
    screenshots: {
      // turned off by default
      basePath: 'homepage', // absolute or relative; excluding file extension
      // type: 'jpeg', // jpeg or png, png default
      // quality: 20 // only applies for jpeg type
      // -> these settings will produce homepage-before.jpg and homepage-after.jpg
    }
})
.then(criticalCss => {
    //fs.writeFileSync('outfile.css', criticalCss);
	console.log(criticalCss);
})
.catch(err => {
console.log(err);
})
