#!/usr/bin/env perl

use v5.14;
use File::Basename;

my $root = dirname(__FILE__) . '/../_site/diagrams';
open(FP, ">$root/index.html") or die $!;

say FP '<ul>';
for (<$root/*.svg>) {
    my $name = basename($_);
    say FP "<li><a href='$name'>$name</a></li>";
}
say FP '</ul>';
close FP;

