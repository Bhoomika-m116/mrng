/**
 * OFFICIAL LEGAL PORTAL - JAVASCRIPT ENGINE
 * Handles: TTS Audio Narrator, Live Accuracy Counter, Sample Loaders, Clipboard
 */

document.addEventListener('DOMContentLoaded', function () {
    initAccuracyCounter();
    initSpeechSynthesis();
    initSummarySlider();
    initDropzone();
});

// 1. Smooth Animated Counter for Extractive Accuracy Score
function initAccuracyCounter() {
    const counterElem = document.getElementById('accuracyCounter');
    if (!counterElem) return;

    const targetVal = parseFloat(counterElem.getAttribute('data-target') || '0');
    let currentVal = 0;
    const duration = 1400; // ms
    const stepTime = 20;
    const increment = targetVal / (duration / stepTime);

    const timer = setInterval(() => {
        currentVal += increment;
        if (currentVal >= targetVal) {
            currentVal = targetVal;
            clearInterval(timer);
        }
        counterElem.innerText = currentVal.toFixed(1) + '%';
    }, stepTime);
}

// 2. Web Speech API - Legal Executive Summary Audio Narrator
let speechUtterance = null;
let isSpeaking = false;
let isPaused = false;

function initSpeechSynthesis() {
    const playBtn = document.getElementById('playTtsBtn');
    const pauseBtn = document.getElementById('pauseTtsBtn');
    const stopBtn = document.getElementById('stopTtsBtn');

    if (!playBtn) return;

    if (!('speechSynthesis' in window)) {
        const widget = document.getElementById('audioWidget');
        if (widget) widget.style.display = 'none';
        return;
    }

    playBtn.addEventListener('click', function () {
        const summaryElem = document.getElementById('summaryContentText');
        if (!summaryElem) return;

        const textToRead = summaryElem.innerText;

        if (isPaused) {
            window.speechSynthesis.resume();
            isPaused = false;
            isSpeaking = true;
            updateTtsUI('playing');
            return;
        }

        if (window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
        }

        speechUtterance = new SpeechSynthesisUtterance(textToRead);
        speechUtterance.rate = 0.95; // Official clear cadence
        speechUtterance.pitch = 1.0;

        // Try to pick natural English voice
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('David')));
        if (preferredVoice) {
            speechUtterance.voice = preferredVoice;
        }

        speechUtterance.onstart = function () {
            isSpeaking = true;
            isPaused = false;
            updateTtsUI('playing');
        };

        speechUtterance.onend = function () {
            isSpeaking = false;
            isPaused = false;
            updateTtsUI('stopped');
        };

        speechUtterance.onerror = function () {
            isSpeaking = false;
            isPaused = false;
            updateTtsUI('stopped');
        };

        window.speechSynthesis.speak(speechUtterance);
    });

    if (pauseBtn) {
        pauseBtn.addEventListener('click', function () {
            if (window.speechSynthesis.speaking && !isPaused) {
                window.speechSynthesis.pause();
                isPaused = true;
                isSpeaking = false;
                updateTtsUI('paused');
            }
        });
    }

    if (stopBtn) {
        stopBtn.addEventListener('click', function () {
            if (window.speechSynthesis.speaking) {
                window.speechSynthesis.cancel();
            }
            isSpeaking = false;
            isPaused = false;
            updateTtsUI('stopped');
        });
    }
}

function updateTtsUI(state) {
    const statusText = document.getElementById('ttsStatusText');
    const playBtn = document.getElementById('playTtsBtn');
    if (!statusText || !playBtn) return;

    if (state === 'playing') {
        statusText.innerHTML = '<span class="badge bg-success"><i class="bi bi-volume-up-fill me-1"></i>Narrating Summary...</span>';
        playBtn.classList.add('btn-light');
        playBtn.classList.remove('btn-outline-light');
    } else if (state === 'paused') {
        statusText.innerHTML = '<span class="badge bg-warning text-dark"><i class="bi bi-pause-fill me-1"></i>Narration Paused</span>';
    } else {
        statusText.innerHTML = '<span class="badge bg-secondary"><i class="bi bi-headphones me-1"></i>Audio Voice Ready</span>';
        playBtn.classList.add('btn-outline-light');
        playBtn.classList.remove('btn-light');
    }
}

// 3. Interactive Summary Ratio Slider
function initSummarySlider() {
    const slider = document.getElementById('summaryRatioSlider');
    const label = document.getElementById('summaryRatioLabel');
    if (!slider || !label) return;

    slider.addEventListener('input', function () {
        const val = Math.round(parseFloat(slider.value) * 100);
        let desc = "Balanced Executive (25%)";
        if (val <= 15) desc = "Concise Abstract (" + val + "%)";
        else if (val <= 30) desc = "Balanced Executive (" + val + "%)";
        else desc = "Comprehensive In-Depth (" + val + "%)";
        label.innerText = desc;
    });
}

// 4. File Dropzone & Drag Events
function initDropzone() {
    const dropzone = document.getElementById('fileDropzone');
    const fileInput = document.getElementById('documentFileInput');
    const fileInfo = document.getElementById('selectedFileInfo');
    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add('drag-active');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove('drag-active');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            fileInput.files = files;
            showFileSelection(files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            showFileSelection(fileInput.files[0]);
        }
    });

    function showFileSelection(file) {
        if (fileInfo) {
            const sizeKB = (file.size / 1024).toFixed(1);
            fileInfo.innerHTML = `
                <div class="alert alert-success d-flex align-items-center justify-content-between p-2 mt-2 mb-0">
                    <div>
                        <i class="bi bi-file-earmark-check-fill text-success fs-5 me-2"></i>
                        <strong>${file.name}</strong> (${sizeKB} KB)
                    </div>
                    <span class="badge bg-primary">Ready to Extract</span>
                </div>
            `;
        }
    }
}

// 5. One-Click Copy Summary
function copySummaryToClipboard() {
    const summaryElem = document.getElementById('summaryContentText');
    if (!summaryElem) return;

    navigator.clipboard.writeText(summaryElem.innerText).then(() => {
        const copyBtn = document.getElementById('copyBtnText');
        if (copyBtn) {
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="bi bi-check-lg me-1 text-success"></i>Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
            }, 2500);
        }
    });
}

// 6. Realistic Legal Sample Document Loader
const SAMPLE_CONTRACTS = {
    nda: `NON-DISCLOSURE AND CONFIDENTIALITY AGREEMENT

This Non-Disclosure Agreement (the "Agreement") is entered into on this 14th day of October, 2026, by and between Apex Global Solutions Ltd., having its principal office at Financial Towers, Bangalore (hereinafter referred to as the "Disclosing Party"), and CyberCore Technologies Pvt. Ltd., having its registered office at Cyber City, Hyderabad (hereinafter referred to as the "Receiving Party").

WHEREAS, the Disclosing Party possesses certain proprietary trade secrets, proprietary software code algorithms, source data, client portfolios, and confidential commercial evaluations relating to AI document intelligence; and

WHEREAS, the Receiving Party wishes to evaluate potential commercial collaboration and joint licensing, wherein confidential information shall necessarily be disclosed.

NOW, THEREFORE, the parties hereby agree as follows:

1. DEFINITION OF CONFIDENTIAL INFORMATION.
"Confidential Information" shall include all technical, financial, operational, and business data disclosed by the Disclosing Party, whether in oral, written, graphic, or digital form, which is designated as confidential or which reasonably ought to be understood as confidential.

2. OBLIGATIONS OF RECEIVING PARTY.
The Receiving Party agrees to hold and maintain all Confidential Information in strictest confidence. The Receiving Party shall not, without the prior written consent of the Disclosing Party, publish, copy, transmit, reverse engineer, or disclose any Confidential Information to any third party. The Receiving Party agrees to restrict access to Confidential Information strictly to employees who have a bona fide need to know and who are bound by non-disclosure covenants at least as restrictive as this Agreement.

3. INDEMNIFICATION AND LIQUIDATED DAMAGES.
The Receiving Party shall indemnify, defend, and hold harmless the Disclosing Party, its directors, officers, and agents against all losses, damages, liabilities, costs, and attorney fees incurred as a consequence of any breach of confidentiality. In the event of an intentional or unauthorized breach, the Receiving Party agrees to pay liquidated damages of Rs. 25,00,000 without prejudice to the Disclosing Party's right to seek urgent injunctive relief.

4. TERM AND TERMINATION.
This Agreement shall remain in effect for a term of three (3) years from the effective date. Either party may terminate discussions at any time upon thirty (30) days written notice; provided, however, that obligations regarding trade secrets and confidential information shall survive termination in perpetuity.

5. DISPUTE RESOLUTION AND ARBITRATION.
Any controversy or claim arising out of or relating to this Agreement shall be settled by binding arbitration in accordance with the Arbitration and Conciliation Act, 1996. The seat and venue of arbitration shall be Bangalore, Karnataka, India, and proceedings shall be conducted in English by a sole arbitrator mutually appointed by the parties.

6. GOVERNING LAW AND SEVERABILITY.
This Agreement shall be governed by and construed in accordance with the substantive laws of India. If any provision is held invalid or ultra vires by a court of competent jurisdiction, the remaining provisions mutatis mutandis shall continue in full force and effect.`,

    lease: `COMMERCIAL LEASE AND PREMISES AGREEMENT

THIS LEASE AGREEMENT is made and executed on the 1st day of November, 2026, by and between Royal Heights Realty Corporation (hereinafter called the "LESSOR") of the One Part, and Zenith Legal Associates LLP (hereinafter called the "LESSEE") of the Other Part.

1. DEMISED PREMISES AND TERM.
The Lessor hereby demises and leases to the Lessee Office Suite No. 402, measuring approximately 3,500 square feet, located at Supreme Judicial Enclave, New Delhi, for a fixed term of thirty-six (36) consecutive months commencing on November 15, 2026.

2. MONTHLY RENT AND SECURITY DEPOSIT.
The Lessee shall pay to the Lessor a monthly base rent of Rs. 1,85,000 payable in advance on or before the 5th day of each calendar month. The Lessee has furnished an interest-free refundable security deposit of Rs. 11,10,000. Late payments beyond the grace period shall incur liquidated interest penalties at 18% per annum.

3. COVENANTS AND RESTRICTIONS.
The Lessee covenants that the demised premises shall be utilized exclusively for lawful legal advisory and corporate consultancy services. The Lessee shall not assign, sublet, or create any third-party encumbrance or lien upon the premises without prior written consent from the Lessor.

4. INDEMNITY AND LIMITATION OF LIABILITY.
The Lessee agrees to indemnify and hold harmless the Lessor from all claims, civil actions, tortfeasor suits, and liabilities arising from the Lessee's use or negligence within the demised premises. The Lessor's aggregate liability under any circumstance shall be capped strictly at the equivalent of three months' rent.

5. FORCE MAJEURE AND TERMINATION.
Neither party shall be held liable for delay or default occasioned by acts of God, epidemic, war, earthquake, or governmental lockdown. Either party may terminate this lease by providing ninety (90) days advance written notice; provided that default of rent exceeding sixty days empowers the Lessor to initiate immediate unilateral termination and re-entry.

6. GOVERNING LAW AND JURISDICTION.
This Agreement is subject to the exclusive jurisdiction of the Courts of Delhi, India, in accordance with applicable tenancy legislation.`,

    sla: `ENTERPRISE SOFTWARE LICENSE AND SERVICE LEVEL AGREEMENT (SLA)

BETWEEN: NexusCloud Enterprise Systems Inc. ("Vendor") AND Horizon Banking Syndicate ("Client").

1. GRANT OF LICENSE.
Vendor hereby grants to Client a non-exclusive, non-transferable, revocable license to access and deploy the Nexus Legal Automation Suite solely for Client's internal operational requirements. Client shall not decompile, dissemble, or create derivative works.

2. SERVICE LEVEL WARRANTIES AND GUARANTEED UPTIME.
Vendor warrants a minimum 99.9% application availability during each calendar month. In the event of service disruption exceeding acceptable thresholds, Client shall be entitled to service credit disbursements equivalent to 10% of monthly licensing fees.

3. INDEMNIFICATION OF INTELLECTUAL PROPERTY.
Vendor shall defend, indemnify, and hold harmless Client against any third-party legal claims asserting that the software infringes any valid patent, copyright, or trademark.

4. MUTUAL LIMITATION OF LIABILITY.
In no event shall either party be liable for any indirect, incidental, punitive, or consequential damages, or loss of profits. The maximum total liability of either party under this agreement shall not exceed the fees paid in the preceding twelve (12) months.

5. GOVERNING LAW AND ARBITRATION.
This Agreement shall be governed by the laws of India. All disputes shall be finally resolved through expedited arbitration under Indian Arbitration rules.`
};

function loadSampleDocument(type) {
    const textArea = document.getElementById('documentTextArea');
    if (!textArea) return;

    if (SAMPLE_CONTRACTS[type]) {
        textArea.value = SAMPLE_CONTRACTS[type];
        textArea.focus();
        // Visual indicator
        textArea.classList.add('border-primary');
        setTimeout(() => textArea.classList.remove('border-primary'), 800);
    }
}


/* ==========================================================================
   MULTILINGUAL TRANSLATION ENGINE & RISK FACTOR INTERACTION
   ========================================================================== */

let originalEnglishSentences = [];
let translatedSentencesCache = {};
let currentActiveLang = 'en';
let currentActiveViewMode = 'single'; // 'single' or 'bilingual'

document.addEventListener('DOMContentLoaded', function () {
    initTranslationHub();
    initRiskUnderlineControls();
    initBootstrapTooltips();
});

function initBootstrapTooltips() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

function initTranslationHub() {
    // Collect original sentences from the DOM if available
    const originalSentenceNodes = document.querySelectorAll('.summary-sentence-box');
    if (originalSentenceNodes.length > 0) {
        originalEnglishSentences = Array.from(originalSentenceNodes).map(node => {
            const rawText = node.getAttribute('data-original-text') || node.innerText.replace(/^\d+\.\s*/, '').trim();
            return rawText;
        });
    }

    const langButtons = document.querySelectorAll('.lang-pill-btn[data-lang-code]');
    const langSelectDropdown = document.getElementById('nativeLangSelectDropdown');
    const viewModeRadios = document.querySelectorAll('input[name="summaryViewMode"]');

    langButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const langCode = this.getAttribute('data-lang-code');
            selectNativeLanguage(langCode);
        });
    });

    if (langSelectDropdown) {
        langSelectDropdown.addEventListener('change', function () {
            if (this.value) {
                selectNativeLanguage(this.value);
            }
        });
    }

    viewModeRadios.forEach(radio => {
        radio.addEventListener('change', function () {
            currentActiveViewMode = this.value;
            renderSummaryView();
        });
    });
}

function selectNativeLanguage(langCode) {
    if (langCode === currentActiveLang && translatedSentencesCache[langCode]) {
        return;
    }

    // Update active button state
    document.querySelectorAll('.lang-pill-btn').forEach(b => {
        if (b.getAttribute('data-lang-code') === langCode) {
            b.classList.add('active');
        } else {
            b.classList.remove('active');
        }
    });

    const langDropdown = document.getElementById('nativeLangSelectDropdown');
    if (langDropdown) {
        langDropdown.value = langCode;
    }

    currentActiveLang = langCode;

    // If English, render original immediately
    if (langCode === 'en') {
        const currentLangBadge = document.getElementById('currentLangBadge');
        if (currentLangBadge) {
            currentLangBadge.innerHTML = '<span class="badge bg-secondary"><i class="bi bi-globe me-1"></i>English (Original)</span>';
        }
        renderSummaryView();
        return;
    }

    // If already in cache, render immediately
    if (translatedSentencesCache[langCode]) {
        updateLanguageBadge(translatedSentencesCache[langCode].meta);
        renderSummaryView();
        return;
    }

    // Otherwise, fetch from translation API
    showTranslationLoading(true);

    fetch('/api/translate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            target_lang: langCode,
            sentences: originalEnglishSentences
        })
    })
    .then(res => res.json())
    .then(data => {
        showTranslationLoading(false);
        if (data.success) {
            translatedSentencesCache[langCode] = {
                sentences: data.translated_sentences,
                text: data.translated_text,
                meta: {
                    name: data.lang_name,
                    native: data.native_name,
                    flag: data.flag,
                    code: data.target_lang
                }
            };
            updateLanguageBadge(translatedSentencesCache[langCode].meta);
            renderSummaryView();
        } else {
            alert('Translation temporarily unavailable. Please try again or use English original.');
        }
    })
    .catch(err => {
        showTranslationLoading(false);
        console.error('Translation error:', err);
    });
}

function updateLanguageBadge(meta) {
    const currentLangBadge = document.getElementById('currentLangBadge');
    if (currentLangBadge && meta) {
        currentLangBadge.innerHTML = `<span class="badge bg-warning text-dark"><span class="me-1">${meta.flag}</span>${meta.native} (${meta.name})</span>`;
    }
}

function showTranslationLoading(isLoading) {
    const loadingElem = document.getElementById('translationLoadingSpinner');
    const summaryContainer = document.getElementById('summaryContentText');
    if (!loadingElem || !summaryContainer) return;

    if (isLoading) {
        loadingElem.style.display = 'block';
        summaryContainer.style.opacity = '0.4';
    } else {
        loadingElem.style.display = 'none';
        summaryContainer.style.opacity = '1';
    }
}

function renderSummaryView() {
    const container = document.getElementById('summaryContentText');
    if (!container) return;

    const isEnglish = currentActiveLang === 'en';
    const translatedData = translatedSentencesCache[currentActiveLang];

    // 1. English Original View
    if (isEnglish) {
        const originalBoxes = document.querySelectorAll('.summary-sentence-box');
        if (originalBoxes.length > 0) {
            // Restore original HTML
            originalBoxes.forEach(b => b.style.display = 'block');
            const bilingualContainer = document.getElementById('bilingualViewContainer');
            if (bilingualContainer) bilingualContainer.style.display = 'none';
            const nativeOnlyContainer = document.getElementById('nativeOnlyContainer');
            if (nativeOnlyContainer) nativeOnlyContainer.style.display = 'none';
            const defaultList = document.getElementById('defaultSentenceList');
            if (defaultList) defaultList.style.display = 'block';
        }
        return;
    }

    if (!translatedData) return;

    // Hide original default list
    const defaultList = document.getElementById('defaultSentenceList');
    if (defaultList) defaultList.style.display = 'none';

    let nativeContainer = document.getElementById('nativeOnlyContainer');
    if (!nativeContainer) {
        nativeContainer = document.createElement('div');
        nativeContainer.id = 'nativeOnlyContainer';
        container.appendChild(nativeContainer);
    }

    let bilingualContainer = document.getElementById('bilingualViewContainer');
    if (!bilingualContainer) {
        bilingualContainer = document.createElement('div');
        bilingualContainer.id = 'bilingualViewContainer';
        container.appendChild(bilingualContainer);
    }

    if (currentActiveViewMode === 'bilingual') {
        nativeContainer.style.display = 'none';
        bilingualContainer.style.display = 'block';

        let bilingualHTML = '';
        originalEnglishSentences.forEach((enSent, idx) => {
            const transSent = (translatedData.sentences && translatedData.sentences[idx]) ? translatedData.sentences[idx] : '';
            bilingualHTML += `
                <div class="bilingual-row">
                    <div class="bilingual-col-en">
                        <small class="text-muted fw-bold d-block mb-1"><i class="bi bi-file-text me-1"></i>ENGLISH CLAUSE ${idx + 1}</small>
                        ${enSent}
                    </div>
                    <div class="bilingual-col-native">
                        <small class="text-warning-emphasis fw-bold d-block mb-1"><i class="bi bi-translate me-1"></i>${translatedData.meta.native} (CLAUSE ${idx + 1})</small>
                        <strong>${transSent}</strong>
                    </div>
                </div>
            `;
        });
        bilingualContainer.innerHTML = bilingualHTML;

    } else {
        // Native Only View
        bilingualContainer.style.display = 'none';
        nativeContainer.style.display = 'block';

        let nativeHTML = '';
        translatedData.sentences.forEach((sent, idx) => {
            nativeHTML += `
                <div class="summary-sentence-box border-warning" style="background: #FFFDF5;">
                    <span class="text-warning-emphasis fw-bold me-2">${idx + 1}.</span>
                    <span class="native-translated-text" style="font-size: 1.05rem; line-height: 1.8;">${sent}</span>
                </div>
            `;
        });
        nativeContainer.innerHTML = nativeHTML;
    }
}

// 2. Risk Underline Controls and Jump Anchors
function initRiskUnderlineControls() {
    const toggleUnderlinesSwitch = document.getElementById('toggleRiskUnderlines');
    const summaryCardBody = document.getElementById('summaryCardBody');

    if (toggleUnderlinesSwitch && summaryCardBody) {
        toggleUnderlinesSwitch.addEventListener('change', function () {
            if (this.checked) {
                summaryCardBody.classList.remove('hide-risk-underlines');
            } else {
                summaryCardBody.classList.add('hide-risk-underlines');
            }
        });
    }

    // Attach click handlers to risk factor registry pills
    const riskPills = document.querySelectorAll('.risk-factor-registry-pill[data-target-sentence]');
    riskPills.forEach(pill => {
        pill.addEventListener('click', function () {
            const sentIndex = this.getAttribute('data-target-sentence');
            const targetSentenceBox = document.querySelector(`.summary-sentence-box[data-sentence-index="${sentIndex}"]`);
            if (targetSentenceBox) {
                targetSentenceBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
                targetSentenceBox.classList.add('flash-highlight');
                setTimeout(() => targetSentenceBox.classList.remove('flash-highlight'), 2200);
            }
        });
    });

    // Clicking an underlined risk factor also triggers smooth highlight
    document.addEventListener('click', function (e) {
        const factor = e.target.closest('.risk-underlined-factor');
        if (factor) {
            const sentBox = factor.closest('.summary-sentence-box');
            if (sentBox) {
                sentBox.classList.add('flash-highlight');
                setTimeout(() => sentBox.classList.remove('flash-highlight'), 1800);
            }
        }
    });
}
