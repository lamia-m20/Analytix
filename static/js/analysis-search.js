(function () {
    'use strict';

    function initializeAnalysisSearch() {
        if (!window.AnalytixSearch) return;
        window.AnalytixSearch.createSearch({
            inputSelector: '#analytix-page-search',
            formSelector: '#analysis-search-form',
            buttonSelector: '#analysis-search-button',
            noResultsSelector: '#analysis-search-no-results',
            itemSelector: '[data-search-title]'
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeAnalysisSearch, { once: true });
    } else {
        initializeAnalysisSearch();
    }
})();
