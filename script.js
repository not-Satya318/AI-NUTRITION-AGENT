/**
 * NutriAI — Client-side JavaScript
 *
 * Responsibilities:
 *  1. Form validation
 *  2. Option-card selection state
 *  3. BMI calculator (no server round-trip)
 *  4. Loading state during form submission
 */

/* ============================================================
   1. OPTION CARDS — visual selection state
   ============================================================ */
document.querySelectorAll('.option-card').forEach(function (card) {
  var radio = card.querySelector('input[type="radio"]');

  // Click handler
  card.addEventListener('click', function () {
    // Deselect siblings in the same group
    var name = radio ? radio.name : null;
    if (name) {
      document.querySelectorAll('input[name="' + name + '"]').forEach(function (r) {
        r.closest('.option-card') && r.closest('.option-card').classList.remove('selected');
      });
    }
    card.classList.add('selected');
    if (radio) radio.checked = true;

    // Clear any error on the group
    var errEl = document.getElementById('err-' + (radio ? radio.name : ''));
    if (errEl) errEl.textContent = '';
    card.classList.remove('is-invalid');
  });

  // Keyboard accessibility
  card.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      card.click();
    }
  });

  // Restore state on page back navigation
  if (radio && radio.checked) {
    card.classList.add('selected');
  }
});


/* ============================================================
   2. FORM VALIDATION
   ============================================================ */
var form = document.getElementById('nutritionForm');

function showError(fieldId, message) {
  var errEl = document.getElementById('err-' + fieldId);
  var inputEl = document.getElementById(fieldId);
  if (errEl) errEl.textContent = message;
  if (inputEl) inputEl.classList.add('is-invalid');
}

function clearError(fieldId) {
  var errEl = document.getElementById('err-' + fieldId);
  var inputEl = document.getElementById(fieldId);
  if (errEl) errEl.textContent = '';
  if (inputEl) inputEl.classList.remove('is-invalid');
}

function clearAllErrors() {
  document.querySelectorAll('.field-error').forEach(function (el) {
    el.textContent = '';
  });
  document.querySelectorAll('.is-invalid').forEach(function (el) {
    el.classList.remove('is-invalid');
  });
}

function validateForm() {
  var isValid = true;
  clearAllErrors();

  /* ── Name ── */
  var name = document.getElementById('name');
  if (!name || !name.value.trim()) {
    showError('name', 'Please enter your name.');
    isValid = false;
  }

  /* ── Age ── */
  var age = document.getElementById('age');
  if (!age || !age.value.trim()) {
    showError('age', 'Please enter your age.');
    isValid = false;
  } else {
    var ageVal = parseInt(age.value, 10);
    if (isNaN(ageVal) || ageVal < 1 || ageVal > 120) {
      showError('age', 'Age must be a whole number between 1 and 120.');
      isValid = false;
    }
  }

  /* ── Gender ── */
  var gender = document.getElementById('gender');
  if (!gender || !gender.value) {
    showError('gender', 'Please select your gender.');
    isValid = false;
  }

  /* ── Height ── */
  var height = document.getElementById('height');
  if (!height || !height.value.trim()) {
    showError('height', 'Please enter your height.');
    isValid = false;
  } else {
    var hVal = parseFloat(height.value);
    if (isNaN(hVal) || hVal < 50 || hVal > 300) {
      showError('height', 'Height must be between 50 and 300 cm.');
      isValid = false;
    }
  }

  /* ── Weight ── */
  var weight = document.getElementById('weight');
  if (!weight || !weight.value.trim()) {
    showError('weight', 'Please enter your weight.');
    isValid = false;
  } else {
    var wVal = parseFloat(weight.value);
    if (isNaN(wVal) || wVal < 10 || wVal > 500) {
      showError('weight', 'Weight must be between 10 and 500 kg.');
      isValid = false;
    }
  }

  /* ── Activity Level ── */
  var activity = document.querySelector('input[name="activity_level"]:checked');
  if (!activity) {
    var errActivity = document.getElementById('err-activity_level');
    if (errActivity) errActivity.textContent = 'Please select your activity level.';
    isValid = false;
  }

  /* ── Fitness Goal ── */
  var goal = document.querySelector('input[name="fitness_goal"]:checked');
  if (!goal) {
    var errGoal = document.getElementById('err-fitness_goal');
    if (errGoal) errGoal.textContent = 'Please select your fitness goal.';
    isValid = false;
  }

  /* ── Food Preference ── */
  var pref = document.querySelector('input[name="food_preference"]:checked');
  if (!pref) {
    var errPref = document.getElementById('err-food_preference');
    if (errPref) errPref.textContent = 'Please select your food preference.';
    isValid = false;
  }

  return isValid;
}

/* Inline real-time validation on blur */
['name', 'age', 'height', 'weight', 'gender'].forEach(function (id) {
  var el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('blur', function () {
    validateForm();
  });
  el.addEventListener('input', function () {
    clearError(id);
  });
});


/* ── Submit handler ── */
if (form) {
  form.addEventListener('submit', function (e) {
    if (!validateForm()) {
      e.preventDefault();
      // Scroll to first error
      var firstErr = document.querySelector('.is-invalid, .field-error:not(:empty)');
      if (firstErr) {
        firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }

    /* Show loading state */
    var btn = document.getElementById('submitBtn');
    var loadingText = document.getElementById('loadingText');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Generating…';
    }
    if (loadingText) {
      loadingText.hidden = false;
    }
  });
}


/* ============================================================
   3. BMI CALCULATOR
   ============================================================ */
function calculateBMI() {
  var heightInput = document.getElementById('bmi-height');
  var weightInput = document.getElementById('bmi-weight');
  var ageInput    = document.getElementById('bmi-age');
  var resultDiv   = document.getElementById('bmi-result');

  if (!heightInput || !weightInput || !resultDiv) return;

  var h   = parseFloat(heightInput.value);
  var w   = parseFloat(weightInput.value);
  var age = ageInput ? parseInt(ageInput.value, 10) : null;

  /* Validate */
  if (isNaN(h) || h < 50 || h > 300) {
    resultDiv.hidden = false;
    resultDiv.innerHTML = '<p style="color:var(--danger);font-size:.85rem;">' +
      'Please enter a valid height (50–300 cm).</p>';
    return;
  }
  if (isNaN(w) || w < 10 || w > 500) {
    resultDiv.hidden = false;
    resultDiv.innerHTML = '<p style="color:var(--danger);font-size:.85rem;">' +
      'Please enter a valid weight (10–500 kg).</p>';
    return;
  }

  /* Under-18 guard */
  if (age !== null && !isNaN(age) && age < 18) {
    resultDiv.hidden = false;
    resultDiv.innerHTML =
      '<p style="font-size:.85rem;color:#01579b;">' +
      '<strong>Note for under-18:</strong> BMI categories for children and teenagers ' +
      'depend on age- and sex-specific growth charts. Please consult a parent/guardian ' +
      'and a qualified healthcare professional for an accurate assessment.</p>';
    return;
  }

  /* Calculate */
  var hm  = h / 100;
  var bmi = Math.round((w / (hm * hm)) * 10) / 10;

  var category, colour;
  if (bmi < 18.5)      { category = 'Underweight'; colour = '#0288d1'; }
  else if (bmi < 25.0) { category = 'Normal range'; colour = '#2e7d32'; }
  else if (bmi < 30.0) { category = 'Overweight';   colour = '#f57f17'; }
  else                 { category = 'Obesity';       colour = '#c62828'; }

  resultDiv.hidden = false;
  resultDiv.innerHTML =
    '<div class="bmi-number" style="color:' + colour + ';">' + bmi + '</div>' +
    '<div class="bmi-cat" style="color:' + colour + ';">' + category + '</div>' +
    '<p style="font-size:.72rem;color:var(--muted);margin-top:6px;">' +
    'BMI is a screening tool only — not a medical diagnosis.</p>';
}

/* Allow pressing Enter inside BMI fields */
['bmi-height', 'bmi-weight', 'bmi-age'].forEach(function (id) {
  var el = document.getElementById(id);
  if (el) {
    el.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); calculateBMI(); }
    });
  }
});


/* ============================================================
   4. AUTO-FILL FORM HEIGHT/WEIGHT FROM BMI CALCULATOR
      (convenience: sync the sidebar inputs to the main form)
   ============================================================ */
var bmiHeightEl = document.getElementById('bmi-height');
var bmiWeightEl = document.getElementById('bmi-weight');
var formHeightEl = document.getElementById('height');
var formWeightEl = document.getElementById('weight');

if (bmiHeightEl && formHeightEl) {
  bmiHeightEl.addEventListener('change', function () {
    if (!formHeightEl.value) formHeightEl.value = bmiHeightEl.value;
  });
}
if (bmiWeightEl && formWeightEl) {
  bmiWeightEl.addEventListener('change', function () {
    if (!formWeightEl.value) formWeightEl.value = bmiWeightEl.value;
  });
}
