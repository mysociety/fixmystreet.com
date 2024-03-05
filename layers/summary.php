<?php

$ROOT = dirname(__FILE__) . '/../../';

$DIR = $ROOT . 'fixmystreet.com/layers';
$i = new \RecursiveDirectoryIterator($DIR);
$i = new \RegexIterator($i, '/\.map$/');
$i = iterator_to_array($i);
usort($i, function($a, $b) { return $a->getPathname() > $b->getPathname(); });

$used_layers = [];
foreach ($i as $map) {
	$layers = parse_layers($map);
	$used_layers = array_merge($used_layers, $layers);
}

$DIR = $ROOT . 'layers/';
$i = new \RecursiveDirectoryIterator($DIR);
$i = new \RecursiveIteratorIterator($i);
$i = new \RegexIterator($i, '/\.(shp|gpkg|tab)$/i');
$i = iterator_to_array($i);
usort($i, function($a, $b) {
	$a = $a->getPathname();
	$b = $b->getPathname();
	return [substr_count($a, '/'), $a] <=> [substr_count($b, '/'), $b];
});

$out = [];
foreach ($i as $d) {
	$ogr = `ogrinfo -ro -al -so '$d'`;
	$data = parse_ogr($ogr);
	if (!$data['date']) $data['date'] = filemtime($d);
	$data['directory'] = str_replace($DIR, '', $d->getPathInfo());
	$fn = str_replace($DIR, '', $d);
	if (array_key_exists($fn, $used_layers)) {
		$data['in_use'] = $used_layers[$fn];
	}
	$out[$fn] = $data;
}

$j = json_encode($out, JSON_PRETTY_PRINT);
# Store in two places so can be looked up depending
file_put_contents($DIR . 'summary.json', $j);
file_put_contents($ROOT . 'tilma/web/layers.json', $j);

function parse_ogr($ogr) {
	preg_match('#^INFO: Open.*\n *using driver.*successful\.\n\nLayer name: (.*?)\n(?:Metadata:\n  DBF_DATE_LAST_UPDATE=(.*?)\n)?Geometry: (.*?)\nFeature Count: (.*?)\n(?:Extent: (.*?)\n)?Layer SRS WKT:\n(?:\(unknown\)|(?:GEOGCR?S|PROJCR?S|COMPOUNDCRS).*?(?:1936|WGS 84).*\]\])\n(.*)#s', $ogr, $m);
if (!$m) { print $ogr; exit; }
	preg_match_all('#^(.*?): .*?$#m', $m[6], $mm);
	return [
		'name' => $m[1],
		'date' => strtotime($m[2]),
		'geometry' => $m[3],
		'features' => $m[4],
		'extent' => $m[5],
		'fields' => $mm[1],
	];
}

function parse_layers($map) {
	$state = [];
	$layer = '';
	$used = [];
	foreach (file($map) as $line) {
		$line = trim($line);
		if (!$line) {
			continue;
		}
		if (preg_match('/^END/', $line)) {
			$fin = array_pop($state);
			if ($fin == 'LAYER') {
				preg_match("#NAME ['\"](.*?)['\"]#", $layer, $m);
				$name = $m[1];
				if (preg_match("#CONNECTIONTYPE UNION#", $layer)) {
					# Nothing
				} elseif (preg_match("#CONNECTION ['\"](.*?)['\"]#", $layer, $m)) {
					$used[str_replace('../../layers/', '', $m[1])] = $name;
				} elseif (preg_match("#^DATA ['\"](.*?)['\"]#m", $layer, $m)) {
					$used["$m[1].shp"] = $name;
				}
				$layer = '';
			}
		} elseif (in_array($line, ['MAP', 'OUTPUTFORMAT', 'LAYER', 'PROJECTION', 'METADATA', 'WEB', 'CLASS', 'STYLE'])) {
			$state[] = $line;
		} elseif (end($state) == 'LAYER') {
			$layer .= "$line\n";
		}
	}
	return $used;
}
