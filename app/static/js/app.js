/**
 * UniCycle — Vue 3 Application (Vanilla JS, no build step)
 *
 * Two mount points:
 *   #list-item-app  → "List an Item" form (kg saved preview + image upload preview)
 *   #marketplace-app → (reserved for future client-side filtering — currently server-side)
 */

// ──────────────────────────────────────────────
// Category weights mapping (kg saved per category)
// ──────────────────────────────────────────────
const CATEGORY_WEIGHTS = {
    "Furniture":    12.0,
    "Kitchenware":   4.0,
    "Electronics":   3.0,
    "Sports":        2.5,
    "Clothing":      1.5,
    "Books":         0.8,
    "Stationery":    0.3,
    "Other":         1.0,
};


// ──────────────────────────────────────────────
// List Item App
// ──────────────────────────────────────────────
const ListItemApp = {
    delimiters: ["[[", "]]"],

    data() {
        return {
            selectedCategory: "",
            isFree: false,
            imagePreview: null,
        };
    },

    computed: {
        kgSaved() {
            return CATEGORY_WEIGHTS[this.selectedCategory] || 0;
        },
    },

    methods: {
        onFileSelect(event) {
            const file = event.target.files[0];
            this.previewFile(file);
        },

        onDrop(event) {
            const file = event.dataTransfer.files[0];
            if (file) {
                this.$refs.fileInput.files = event.dataTransfer.files;
                this.previewFile(file);
            }
        },

        previewFile(file) {
            if (!file) return;

            // Validate type
            const allowed = ["image/jpeg", "image/png", "image/webp"];
            if (!allowed.includes(file.type)) {
                alert("Please upload a JPG, PNG, or WebP image.");
                return;
            }

            // Show preview
            const reader = new FileReader();
            reader.onload = (e) => {
                this.imagePreview = e.target.result;
            };
            reader.readAsDataURL(file);
        },
    },
};

// Mount List Item app if element exists
const listItemEl = document.getElementById("list-item-app");
if (listItemEl) {
    Vue.createApp(ListItemApp).mount("#list-item-app");
}
