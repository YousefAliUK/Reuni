/**
 * Reuni — Listing & Editing Item Form Logic (CSP-safe)
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if this is an item form page
    const form = document.querySelector('.auth-card form, .list-item-container form, form[action*="list"], form[action*="edit"]');
    if (!form) return;

    const categoryWeightsScript = document.getElementById('category-weights');
    let categoryWeights = {};
    if (categoryWeightsScript) {
        try {
            categoryWeights = JSON.parse(categoryWeightsScript.textContent);
        } catch(e) {
            console.error('Error parsing category weights:', e);
        }
    }

    // ── 1. Character Counters ──
    const titleInput = document.getElementById('title');
    const titleCounter = document.getElementById('title-char-counter');
    if (titleInput && titleCounter) {
        titleCounter.textContent = `${titleInput.value.length}/80`;
        titleInput.addEventListener('input', function() {
            titleCounter.textContent = `${titleInput.value.length}/80`;
        });
    }

    const descInput = document.getElementById('description');
    const descCounter = document.getElementById('desc-char-counter');
    if (descInput && descCounter) {
        descCounter.textContent = `${descInput.value.length}/2000`;
        descInput.addEventListener('input', function() {
            descCounter.textContent = `${descInput.value.length}/2000`;
        });
    }

    // ── 2. Category Weights Preview ──
    const categorySelect = document.getElementById('category');
    const liveEcoPreview = document.getElementById('live-eco-preview');
    const liveEcoText = document.getElementById('live-eco-text');

    function updateEcoPreview() {
        if (!categorySelect || !liveEcoPreview || !liveEcoText) return;
        const category = categorySelect.value;
        if (category && categoryWeights[category] !== undefined) {
            const w = categoryWeights[category];
            liveEcoText.textContent = `Selecting '${category}' saves ~${w.toFixed(1)} kg CO₂e prevented`;
            liveEcoPreview.classList.add('eco-preview-banner--visible');
        } else {
            liveEcoPreview.classList.remove('eco-preview-banner--visible');
        }
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', updateEcoPreview);
        updateEcoPreview(); // Initial check
    }

    // ── 3. Condition Segmented Buttons ──
    const conditionSelect = document.getElementById('condition');
    const conditionBtns = document.querySelectorAll('.condition-btn');
    if (conditionSelect && conditionBtns.length) {
        conditionBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                conditionSelect.value = btn.dataset.value;
                conditionBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
        
        // Set initial selected if present
        if (conditionSelect.value) {
            const active = Array.from(conditionBtns).find(b => b.dataset.value === conditionSelect.value);
            if (active) active.classList.add('active');
        }
    }

    // ── 4. Free vs Paid Segmented Switcher ──
    const isFreeCheckbox = document.getElementById('is_free');
    const priceToggleFree = document.getElementById('price-toggle-free');
    const priceTogglePaid = document.getElementById('price-toggle-paid');
    const priceInputContainer = document.getElementById('price-input-container');
    const priceInput = document.getElementById('price');

    function setPriceMode(isFree) {
        if (!isFreeCheckbox) return;
        isFreeCheckbox.checked = isFree;
        
        if (isFree) {
            if (priceToggleFree) priceToggleFree.classList.add('active-free');
            if (priceTogglePaid) priceTogglePaid.classList.remove('active-paid');
            if (priceInputContainer) priceInputContainer.style.display = 'none';
            if (priceInput) {
                priceInput.value = '';
                priceInput.required = false;
            }
        } else {
            if (priceToggleFree) priceToggleFree.classList.remove('active-free');
            if (priceTogglePaid) priceTogglePaid.classList.add('active-paid');
            if (priceInputContainer) priceInputContainer.style.display = 'block';
            if (priceInput) priceInput.required = true;
        }
    }

    if (priceToggleFree && priceTogglePaid && isFreeCheckbox) {
        priceToggleFree.addEventListener('click', () => setPriceMode(true));
        priceTogglePaid.addEventListener('click', () => setPriceMode(false));
        
        // Initial price state
        setPriceMode(isFreeCheckbox.checked !== false);
    }

    // ── 5. Image Upload Preview Zone & Remove Button ──
    const uploadZone = document.getElementById('photo-upload-zone');
    if (uploadZone) {
        const fileInput = uploadZone.querySelector('input[type="file"]');
        const uploadPlaceholder = document.getElementById('upload-placeholder');
        const photoPreview = document.getElementById('photo-preview');
        const removePhotoBtn = document.getElementById('remove-photo-btn');

        if (fileInput) {
            uploadZone.addEventListener('click', (e) => {
                if (e.target !== fileInput && e.target !== removePhotoBtn) {
                    fileInput.click();
                }
            });

            uploadZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadZone.classList.add('dragover');
            });

            uploadZone.addEventListener('dragleave', () => {
                uploadZone.classList.remove('dragover');
            });

            uploadZone.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadZone.classList.remove('dragover');
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    fileInput.files = e.dataTransfer.files;
                    previewFile(e.dataTransfer.files[0]);
                }
            });

            fileInput.addEventListener('change', () => {
                if (fileInput.files && fileInput.files[0]) {
                    previewFile(fileInput.files[0]);
                }
            });

            if (removePhotoBtn) {
                removePhotoBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    fileInput.value = '';
                    if (photoPreview) {
                        photoPreview.src = '';
                        photoPreview.style.display = 'none';
                    }
                    removePhotoBtn.style.display = 'none';
                    if (uploadPlaceholder) uploadPlaceholder.style.display = 'flex';
                });
            }

            function previewFile(file) {
                const allowed = ['image/jpeg', 'image/png', 'image/webp'];
                if (!allowed.includes(file.type)) {
                    alert('Please upload a JPG, PNG, or WebP image.');
                    return;
                }
                const reader = new FileReader();
                reader.onload = function(e) {
                    if (photoPreview) {
                        photoPreview.src = e.target.result;
                        photoPreview.style.display = 'block';
                    }
                    if (removePhotoBtn) removePhotoBtn.style.display = 'inline-flex';
                    if (uploadPlaceholder) uploadPlaceholder.style.display = 'none';
                };
                reader.readAsDataURL(file);
            }
        }
    }

    // ── 6. Form Submission Validation & State ──
    form.addEventListener('submit', function(e) {
        let isValid = true;
        
        // Remove previous error styling and messages
        const existingErrors = form.querySelectorAll('.custom-error-msg');
        existingErrors.forEach(el => el.remove());
        
        const photoZone = document.getElementById('photo-upload-zone');
        const condContainer = document.querySelector('.condition-btns-container');
        const categorySelect = document.getElementById('category');
        const titleInput = document.getElementById('title');
        const priceInput = document.getElementById('price');
        
        if (photoZone) photoZone.classList.remove('error');
        if (condContainer) condContainer.classList.remove('error');
        if (categorySelect) categorySelect.classList.remove('error');
        if (titleInput) titleInput.classList.remove('error');
        if (priceInput) priceInput.classList.remove('error');

        // Validate Photo
        const imageInput = document.getElementById('image');
        if (imageInput && imageInput.hasAttribute('required') && imageInput.files.length === 0) {
            isValid = false;
            if (photoZone) {
                photoZone.classList.add('error');
                const errMsg = document.createElement('div');
                errMsg.className = 'custom-error-msg';
                errMsg.textContent = 'Please upload a photo of your item.';
                photoZone.parentNode.appendChild(errMsg);
            }
        }

        // Validate Title
        if (titleInput && !titleInput.value.trim()) {
            isValid = false;
            titleInput.classList.add('error');
            const errMsg = document.createElement('div');
            errMsg.className = 'custom-error-msg';
            errMsg.textContent = 'Please enter a title.';
            titleInput.parentNode.appendChild(errMsg);
        }

        // Validate Category
        if (categorySelect && !categorySelect.value) {
            isValid = false;
            categorySelect.classList.add('error');
            const errMsg = document.createElement('div');
            errMsg.className = 'custom-error-msg';
            errMsg.textContent = 'Please select a category.';
            categorySelect.parentNode.appendChild(errMsg);
        }

        // Validate Condition
        if (conditionSelect && !conditionSelect.value) {
            isValid = false;
            if (condContainer) {
                condContainer.classList.add('error');
                const errMsg = document.createElement('div');
                errMsg.className = 'custom-error-msg';
                errMsg.textContent = 'Please select the condition of your item.';
                condContainer.parentNode.appendChild(errMsg);
            }
        }

        // Validate Price if not free
        if (isFreeCheckbox && !isFreeCheckbox.checked && priceInput) {
            const priceVal = parseFloat(priceInput.value);
            if (isNaN(priceVal) || priceVal <= 0) {
                isValid = false;
                priceInput.classList.add('error');
                const errMsg = document.createElement('div');
                errMsg.className = 'custom-error-msg';
                errMsg.textContent = 'Please enter a price greater than £0.00.';
                priceInput.parentNode.appendChild(errMsg);
            }
        }

        if (!isValid) {
            e.preventDefault();
            // Scroll to the first error element
            const firstError = form.querySelector('.custom-error-msg');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            return false;
        }

        // Disable submit buttons to prevent double click
        const submitBtns = form.querySelectorAll('button[type="submit"]');
        submitBtns.forEach(submitBtn => {
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Saving<span class="warning-pulse">…</span>';
        });
    });

    // ── 7. New Listing Reset on pageshow (list_item only) ──
    const isNewListingForm = form.getAttribute('action') && form.getAttribute('action').includes('list');
    if (isNewListingForm) {
        window.addEventListener('pageshow', function() {
            setTimeout(function() {
                form.reset();
                
                // Re-enable and restore submit button states
                const submitBtns = form.querySelectorAll('button[type="submit"]');
                submitBtns.forEach(btn => {
                    btn.disabled = false;
                    btn.innerHTML = 'List this item';
                });
                
                // Reset text field character counters
                if (titleCounter) titleCounter.textContent = '0/80';
                if (descCounter) descCounter.textContent = '0/2000';
                
                // Hide dynamic live eco preview
                if (liveEcoPreview) liveEcoPreview.classList.remove('eco-preview-banner--visible');
                
                // Reset photo upload area preview state
                const photoPreview = document.getElementById('photo-preview');
                if (photoPreview) {
                    photoPreview.src = '';
                    photoPreview.style.display = 'none';
                }
                const removePhotoBtn = document.getElementById('remove-photo-btn');
                if (removePhotoBtn) removePhotoBtn.style.display = 'none';
                const uploadPlaceholder = document.getElementById('upload-placeholder');
                if (uploadPlaceholder) uploadPlaceholder.style.display = 'flex';
                
                // Reset segmented condition buttons
                if (conditionBtns.length) {
                    conditionBtns.forEach(b => b.classList.remove('active'));
                }
                if (conditionSelect) conditionSelect.value = '';
                
                // Reset segmented price switcher
                setPriceMode(true);
            }, 0);
        });
    }
});
