/**
 * NutriPulse — Client-side JavaScript
 * Theme toggle, settings drawer, image upload, food form, entry deletion
 */

document.addEventListener('DOMContentLoaded', function() {
    setupThemeToggle();
    setupSettingsDrawer();
    setupImageUpload();
    setupFoodForm();
});

// ── Theme Toggle ──

function setupThemeToggle() {
    var toggles = document.querySelectorAll('.theme-toggle');
    toggles.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            var isDark = document.documentElement.classList.toggle('dark');
            localStorage.setItem('nutripulse-theme', isDark ? 'dark' : 'light');
        });
    });

    // Theme option buttons in settings
    var themeOpts = document.querySelectorAll('.theme-opt');
    themeOpts.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var theme = btn.dataset.theme;
            if (theme === 'dark') {
                document.documentElement.classList.add('dark');
                localStorage.setItem('nutripulse-theme', 'dark');
            } else if (theme === 'light') {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('nutripulse-theme', 'light');
            } else {
                localStorage.removeItem('nutripulse-theme');
                var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                if (prefersDark) document.documentElement.classList.add('dark');
                else document.documentElement.classList.remove('dark');
            }
            // Update active state
            themeOpts.forEach(function(b) { b.classList.remove('btn-primary'); b.classList.add('btn-secondary'); });
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-primary');
        });
    });

    // Set initial active theme button
    var current = localStorage.getItem('nutripulse-theme') || 'system';
    themeOpts.forEach(function(btn) {
        if (btn.dataset.theme === current) {
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-primary');
        }
    });
}

// ── Settings Drawer ──

function setupSettingsDrawer() {
    var trigger = document.getElementById('settings-trigger');
    var overlay = document.getElementById('settings-overlay');
    var drawer = document.getElementById('settings-drawer');
    var closeBtn = document.getElementById('settings-close');

    if (!trigger || !overlay || !drawer) return;

    function openDrawer() {
        overlay.classList.add('open');
        drawer.classList.add('open');
    }
    function closeDrawer() {
        overlay.classList.remove('open');
        drawer.classList.remove('open');
    }

    trigger.addEventListener('click', openDrawer);
    overlay.addEventListener('click', closeDrawer);
    if (closeBtn) closeBtn.addEventListener('click', closeDrawer);

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && drawer.classList.contains('open')) closeDrawer();
    });
}

function saveGoal() {
    var input = document.getElementById('settings-calorie-goal');
    var goal = parseInt(input.value);
    if (!goal || goal < 500 || goal > 10000) {
        showToast('Goal must be between 500 and 10000', 'error');
        return;
    }
    fetch('/api/settings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({daily_calorie_goal: goal})
    }).then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.success) {
            showToast('Calorie goal updated');
            var goalDisplay = document.getElementById('goal-display');
            if (goalDisplay) goalDisplay.textContent = goal;
            setTimeout(function() { location.reload(); }, 800);
        } else {
            showToast(data.error || 'Failed to save', 'error');
        }
    });
}

function showToast(message, type) {
    type = type || 'success';
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(function() { toast.remove(); }, 2500);
}

// ── Image Upload + AI Analysis ──

function setupImageUpload() {
    var zone = document.getElementById('upload-zone');
    var input = document.getElementById('food-image');
    if (!zone || !input) return;

    zone.addEventListener('click', function() { input.click(); });

    zone.addEventListener('dragover', function(e) { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', function() { zone.classList.remove('drag-over'); });
    zone.addEventListener('drop', function(e) {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            input.files = e.dataTransfer.files;
            handleImageSelected(e.dataTransfer.files[0]);
        }
    });

    input.addEventListener('change', function() {
        if (input.files.length) handleImageSelected(input.files[0]);
    });
}

function handleImageSelected(file) {
    if (!file || !file.type.startsWith('image/')) {
        showToast('Please select an image file', 'error');
        return;
    }

    var preview = document.getElementById('image-preview');
    var content = document.getElementById('upload-content');
    var reader = new FileReader();
    reader.onload = function(e) {
        preview.src = e.target.result;
        preview.style.display = 'block';
        content.style.display = 'none';
    };
    reader.readAsDataURL(file);

    var loading = document.getElementById('ai-loading');
    var result = document.getElementById('ai-result');
    loading.style.display = 'flex';
    result.style.display = 'none';

    var formData = new FormData();
    formData.append('image', file);

    fetch('/api/food/analyze', { method: 'POST', body: formData })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            loading.style.display = 'none';
            if (data.error) {
                showToast(data.error, 'error');
                return;
            }
            result.style.display = 'block';
            document.getElementById('ai-food-name').textContent = data.food_name;
            document.getElementById('ai-insight').textContent = data.insight || '';
            fillForm(data);
            showToast('Food identified: ' + data.food_name);
        })
        .catch(function() {
            loading.style.display = 'none';
            showToast('Failed to analyze image', 'error');
        });
}

function fillForm(data) {
    var fields = {
        'food_name': data.food_name,
        'calories': Math.round(data.calories || 0),
        'protein': (data.protein || 0).toFixed(1),
        'carbs': (data.carbs || 0).toFixed(1),
        'fat': (data.fat || 0).toFixed(1),
        'fiber': (data.fiber || 0).toFixed(1),
        'serving_size': data.serving_size || '1 serving',
        'health_score': data.health_score || 5,
        'ai_insight': data.insight || '',
        'image_filename': data.image_filename || ''
    };
    for (var id in fields) {
        var el = document.getElementById(id);
        if (el) el.value = fields[id];
    }
}

// ── Food Form Submission ──

function setupFoodForm() {
    var form = document.getElementById('food-form');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        var name = document.getElementById('food_name').value.trim();
        if (!name) { showToast('Food name is required', 'error'); return; }

        var data = {
            food_name: name,
            calories: parseFloat(document.getElementById('calories').value) || 0,
            protein: parseFloat(document.getElementById('protein').value) || 0,
            carbs: parseFloat(document.getElementById('carbs').value) || 0,
            fat: parseFloat(document.getElementById('fat').value) || 0,
            fiber: parseFloat(document.getElementById('fiber').value) || 0,
            serving_size: document.getElementById('serving_size').value || '1 serving',
            meal_type: document.getElementById('meal_type').value,
            health_score: parseInt(document.getElementById('health_score').value) || 5,
            ai_insight: document.getElementById('ai_insight').value || '',
            image_filename: document.getElementById('image_filename').value || ''
        };

        var btn = document.getElementById('submit-food-btn');
        btn.disabled = true;

        fetch('/api/food', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(function(r) { return r.json(); })
        .then(function(result) {
            if (result.success) {
                showToast('Food logged successfully');
                setTimeout(function() { location.reload(); }, 500);
            } else {
                showToast(result.error || 'Failed to save', 'error');
                btn.disabled = false;
            }
        })
        .catch(function() {
            showToast('Failed to save food entry', 'error');
            btn.disabled = false;
        });
    });
}

// ── Delete Entry ──

function deleteEntry(id) {
    if (!confirm('Delete this entry?')) return;
    fetch('/api/food/' + id, { method: 'DELETE' })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.success) {
                var el = document.getElementById('entry-' + id);
                if (el) {
                    el.style.opacity = '0';
                    el.style.transform = 'translateX(20px)';
                    el.style.transition = 'all 0.2s ease';
                    setTimeout(function() { el.remove(); }, 200);
                }
                showToast('Entry deleted');
            }
        });
}
