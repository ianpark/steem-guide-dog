var dataset = {}

function load_status() {
    $.ajax({
        type: 'GET',
        url: "/status",
        success: function( data ) {
            dataset = JSON.parse(data);
            dataset.reporters = dataset.users.filter(function(el) {
                return el[1] > 0;
            });
            dataset.spammers = dataset.users.filter(function(el) {
                return el[2] >= 3;
            });
            var scope = null;
            scope = angular.element($("#reports")).scope();
            scope.$apply(function() {
                scope.dataset = dataset.reports;
            });
            // Handle reporters
            scope = angular.element($("#reporters")).scope();
            scope.$apply(function() {
                scope.dataset = dataset.reporters.sort(function(a, b) {
                    if (a[1] < b[1]) return 1;
                    if (a[1] > b[1]) return -1;
                    return 0;
                });
            });
            scope = angular.element($("#spammers")).scope();
            scope.$apply(function() {
                scope.dataset = dataset.spammers.sort(function(a, b) {
                    if (a[2] < b[2]) return 1;
                    if (a[2] > b[2]) return -1;
                    return 0;
                });
            });
        }
    });
};

$( document ).ready(function() {
    load_status();
});

var app = angular.module('guidedog', []);
app.controller('reporters_ctrl', ['$scope', '$window', function($scope, $window) {
}]);
app.controller('spammers_ctrl', ['$scope', '$window', function($scope, $window) {
}]);
app.controller('reports_ctrl', ['$scope', '$window', function($scope, $window) {
}]);