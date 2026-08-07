(function (global) {
    'use strict';

    function normalizeArabicSearchText(text) {
        return String(text == null ? '' : text)
            .trim()
            .toLocaleLowerCase('ar')
            .replace(/[\u064b-\u065f\u0670]/g, '')
            .replace(/ـ/g, '')
            .replace(/[أإآ]/g, 'ا')
            .replace(/ى/g, 'ي')
            .replace(/\s+/g, ' ');
    }

    function searchableText(element) {
        return normalizeArabicSearchText([
            element.dataset.searchTitle || '',
            element.dataset.searchKeywords || '',
            element.textContent || ''
        ].join(' '));
    }

    function matchScore(entry, query) {
        if (query.length < 2) return 0;
        if (entry.title === query) return 100;
        if (entry.title.includes(query)) return 80;
        if (entry.keywords.includes(query)) return 60;
        const terms = query.split(' ').filter(function (term) { return term.length > 1; });
        if (terms.length > 0 && terms.every(function (term) {
            return entry.content.includes(term);
        })) return 40;
        return entry.content.includes(query) ? 20 : 0;
    }

    function highlightResult(element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        if (typeof element.animate === 'function') {
            element.animate(
                [
                    { outline: '0 solid rgba(37,99,235,0)' },
                    { outline: '4px solid rgba(37,99,235,.30)' },
                    { outline: '0 solid rgba(37,99,235,0)' }
                ],
                { duration: 2000, easing: 'ease-out' }
            );
        }
    }

    function createSearch(options) {
        const input = document.querySelector(options.inputSelector);
        if (!input) return null;
        const form = options.formSelector ? document.querySelector(options.formSelector) : null;
        const button = options.buttonSelector ? document.querySelector(options.buttonSelector) : null;
        const noResults = document.querySelector(options.noResultsSelector);
        const elements = Array.from(document.querySelectorAll(options.itemSelector));
        const index = elements.map(function (element) {
            return {
                element: element,
                title: normalizeArabicSearchText(element.dataset.searchTitle),
                keywords: normalizeArabicSearchText(element.dataset.searchKeywords),
                content: searchableText(element)
            };
        });

        function runSearch() {
            const query = normalizeArabicSearchText(input.value);
            if (noResults) noResults.hidden = true;
            if (query.length < 2) return null;
            const match = index
                .map(function (entry) {
                    return { entry: entry, score: matchScore(entry, query) };
                })
                .filter(function (result) { return result.score > 0; })
                .sort(function (left, right) { return right.score - left.score; })[0];
            if (!match) {
                if (noResults) noResults.hidden = false;
                return null;
            }
            highlightResult(match.entry.element);
            return match.entry.element;
        }

        if (form) {
            form.addEventListener('submit', function (event) {
                event.preventDefault();
                runSearch();
            });
        } else {
            input.addEventListener('keydown', function (event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    runSearch();
                }
            });
        }
        if (button && !form) button.addEventListener('click', runSearch);

        return { index: index, search: runSearch };
    }

    global.AnalytixSearch = {
        normalizeArabicSearchText: normalizeArabicSearchText,
        createSearch: createSearch
    };
})(window);
