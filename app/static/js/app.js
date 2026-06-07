/**
 * Reuni — Frontend Form Interactivity (Pure Vanilla JS, CSP-safe)
 *
 * One mount point:
 *   #list-item-app  → "List/Edit an Item" form (kg saved preview + image upload preview)
 */

document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("list-item-app");
    if (!container) return;

    // 1. Parse Category Weights from the page JSON tag
    let categoryWeights = {};
    const weightsScript = document.getElementById("category-weights");
    if (weightsScript) {
        try {
            categoryWeights = JSON.parse(weightsScript.textContent);
        } catch (e) {
            console.error("Error parsing category weights JSON:", e);
        }
    }

    // 2. Select DOM elements
    const fileInput = container.querySelector('input[type="file"]');
    const imageUploadArea = container.querySelector(".image-upload");
    const categorySelect = container.querySelector("#category");
    const isFreeCheckbox = container.querySelector("#is_free");
    const priceInput = container.querySelector("#price");
    
    // Preview elements
    const previewImage = container.querySelector(".image-upload__preview");
    const uploadPlaceholder = container.querySelector(".image-upload__placeholder");
    const kgSavedDisplay = container.querySelector("#kg-saved-display");
    const ecoPreviewContainer = container.querySelector(".eco-preview");

    // 3. Image preview handling helper
    function showPreview(src) {
        if (previewImage) {
            previewImage.src = src;
            previewImage.style.display = "block";
        }
        if (uploadPlaceholder) {
            uploadPlaceholder.style.display = "none";
        }
        if (imageUploadArea) {
            imageUploadArea.classList.add("image-upload--has-preview");
        }
    }

    function previewFile(file) {
        if (!file) return;
        const allowed = ["image/jpeg", "image/png", "image/webp"];
        if (!allowed.includes(file.type)) {
            alert("Please upload a JPG, PNG, or WebP image.");
            return;
        }
        const reader = new FileReader();
        reader.onload = function (e) {
            showPreview(e.target.result);
        };
        reader.readAsDataURL(file);
    }

    // 4. File input change event
    if (fileInput) {
        fileInput.addEventListener("change", function (e) {
            if (e.target.files && e.target.files[0]) {
                previewFile(e.target.files[0]);
            }
        });
    }

    // 5. Drag and drop events + click triggers
    if (imageUploadArea) {
        // Trigger file input click on upload area click
        imageUploadArea.addEventListener("click", function (e) {
            // Only click if we didn't click the input directly to avoid infinite loop
            if (e.target !== fileInput) {
                fileInput.click();
            }
        });

        imageUploadArea.addEventListener("dragover", function (e) {
            e.preventDefault();
        });

        imageUploadArea.addEventListener("drop", function (e) {
            e.preventDefault();
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                fileInput.files = e.dataTransfer.files;
                previewFile(e.dataTransfer.files[0]);
            }
        });
    }

    // 6. Category weights preview
    function updateKgSaved() {
        if (!categorySelect) return;
        const category = categorySelect.value;
        if (category && categoryWeights[category] !== undefined) {
            const weight = categoryWeights[category];
            if (kgSavedDisplay) {
                kgSavedDisplay.textContent = weight.toFixed(1);
            }
            if (ecoPreviewContainer) {
                ecoPreviewContainer.style.display = "flex";
            }
        } else {
            if (ecoPreviewContainer) {
                ecoPreviewContainer.style.display = "none";
            }
        }
    }

    if (categorySelect) {
        categorySelect.addEventListener("change", updateKgSaved);
    }

    // 7. Free / Price toggle
    function updatePriceState() {
        if (!isFreeCheckbox) return;
        const isFree = isFreeCheckbox.checked;
        if (priceInput) {
            priceInput.disabled = isFree;
            const priceGroup = priceInput.closest(".form__group");
            if (priceGroup) {
                if (isFree) {
                    priceGroup.style.display = "none";
                    priceInput.value = "";
                } else {
                    priceGroup.style.display = "block";
                }
            }
        }
    }

    if (isFreeCheckbox) {
        isFreeCheckbox.addEventListener("change", updatePriceState);
    }

    // 8. Initialization on load
    // Check if there is an existing image URL from the DOM
    if (imageUploadArea && imageUploadArea.dataset.existingImage) {
        showPreview(imageUploadArea.dataset.existingImage);
    }
    
    // Initialise category weight display
    updateKgSaved();
    
    // Initialise price state display
    updatePriceState();
});
