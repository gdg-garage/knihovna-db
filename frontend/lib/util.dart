library tisicknih_util;

import 'dart:html';

bool get runningInDevelopment => window.location.hostname == '127.0.0.1' ||
                              window.location.hostname == 'localhost';

// Can also use [:const String.fromEnvironment('DEBUG') != null:], but this
// doesn't work with WebStorm (which doesn't set debug environment).