(function () {
    const sidebar = document.getElementById('workspace-sidebar');
    const overlay = document.getElementById('workspace-overlay');
    const openButton = document.getElementById('sidebar-toggle');
    const closeButton = document.getElementById('sidebar-close');

    function setSidebar(open) {
        if (!sidebar || !overlay || !openButton) return;
        sidebar.classList.toggle('open', open);
        overlay.classList.toggle('visible', open);
        document.body.classList.toggle('sidebar-open', open);
        openButton.setAttribute('aria-expanded', String(open));
    }

    if (openButton) openButton.addEventListener('click', function () { setSidebar(true); });
    if (closeButton) closeButton.addEventListener('click', function () { setSidebar(false); });
    if (overlay) overlay.addEventListener('click', function () { setSidebar(false); });

    const normalizeArabic = window.AnalytixSearch.normalizeArabicSearchText;
    window.AnalytixSearch.createSearch({
        inputSelector: '#feature-search',
        formSelector: '#feature-search-form',
        buttonSelector: '#feature-search-button',
        noResultsSelector: '#no-search-results',
        itemSelector: '[data-search-title]'
    });

    const assistantQuestion = document.getElementById('assistant-question');
    const assistantSend = document.getElementById('assistant-send');
    const assistantAnswer = document.getElementById('assistant-answer');
    const answers = [
        { terms: ['امكانات', 'يستطيع'], answer: 'يحلل Analytix ملفات Excel، ويفحص جودة البيانات والقيم الفارغة والتكرارات، وينشئ الرسوم ولوحات المعلومات والتقارير القابلة للتصدير.' },
        { terms: ['احلل', 'excel', 'رفع ملف'], answer: 'اضغط «رفع ملف جديد» أو «ابدأ التحليل»، ثم اختر ملف Excel. ستظهر لك مؤشرات الجودة والرسوم والجداول وخيارات التصدير بعد اكتمال التحليل.' },
        { terms: ['pdf'], answer: 'نعم، يدعم Analytix تصدير تقرير PDF منسق يحتوي الملخصات والجداول والرسوم البيانية.' },
        { terms: ['powerpoint', 'ppt', 'pptx'], answer: 'نعم، يمكنك تصدير نتائج التحليل إلى PowerPoint يتضمن المؤشرات والرسوم والتوصيات.' },
        { terms: ['ذكاء', 'اصطناعي', 'مساعد'], answer: 'يتضمن Analytix مساعدًا لتعديل لوحة المعلومات بلغة طبيعية، مثل طلب تحويل مخطط إلى أعمدة أو إضافة مقارنة جديدة.' },
        { terms: ['انواع', 'رسوم', 'مخططات'], answer: 'يدعم Analytix الرسوم الخطية ورسوم الأعمدة والدوائر والمؤشرات، ويختار الشكل المناسب وفق نوع البيانات.' },
        { terms: ['جوده', 'يحسب'], answer: 'تُحسب جودة البيانات من اكتمال الخلايا واتساقها، مع مراعاة القيم الفارغة والصفوف المكررة والمشكلات المكتشفة.' }
    ];

    function answerAssistantQuestion() {
        if (!assistantQuestion || !assistantAnswer) return;
        const question = normalizeArabic(assistantQuestion.value);
        if (!question) return;
        const entry = answers
            .map(function (candidate) {
                const score = candidate.terms.reduce(function (total, term) {
                    return total + (question.includes(normalizeArabic(term)) ? 1 : 0);
                }, 0);
                return { candidate: candidate, score: score };
            })
            .filter(function (result) { return result.score > 0; })
            .sort(function (left, right) { return right.score - left.score; })[0];
        assistantAnswer.textContent = entry ? entry.candidate.answer : 'لا أملك إجابة لهذا السؤال حالياً.';
        assistantAnswer.hidden = false;
    }

    if (assistantSend) assistantSend.addEventListener('click', answerAssistantQuestion);
    if (assistantQuestion) {
        assistantQuestion.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                answerAssistantQuestion();
            }
        });
    }

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') setSidebar(false);
    });
})();
