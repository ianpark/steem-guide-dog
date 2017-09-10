var dataset = {}

function load_status() {
    $.ajax({
        type: 'GET',
        url: "/status",
        success: function( data ) {
            dataset = JSON.parse(data);
            console.log(dataset);
            var scope = null;
            scope = angular.element($("#reports")).scope();
            scope.$apply(function() {
                scope.dataset = dataset.reports;
            });
            // Handle reporters
            scope = angular.element($("#reporters")).scope();
            scope.$apply(function() {
                scope.dataset = dataset.users.sort(function(a, b) {
                    if (a[1] < b[1]) return 1;
                    if (a[1] > b[1]) return -1;
                    return 0;
                });
            });
            scope = angular.element($("#spammers")).scope();
            scope.$apply(function() {
                scope.dataset = dataset.users.sort(function(a, b) {
                    if (a[1] < b[1]) return 1;
                    if (a[1] > b[1]) return -1;
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