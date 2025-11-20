#!/usr/bin/env perl

use v5.14;
use File::Basename;

my $dir = dirname(__FILE__);
my $root = "$dir/../_site/diagrams";

open(FP, "<", "$dir/index.html") or die $!;
my $template = join('', <FP>);
close FP;

my $out = "<ul>\n";
for (<$root/*.svg>) {
    my $name = basename($_);
    $out .= "<li><a href='$name'>$name</a></li>\n";
}
$out .= "</ul>\n";

$template =~ s/CONTENT/$out/;

open(FP, ">", "$root/index.html") or die $!;
print FP $template;
close FP;
