(function () {
  const languageFiles = {
    en: "Language/en.json",
    es: "Language/es.json"
  };
  const translationCache = {};

  async function loadDictionary(lang) {
    if (translationCache[lang]) {
      return translationCache[lang];
    }

    const filePath = languageFiles[lang] || languageFiles.en;
    const response = await fetch(filePath);
    if (!response.ok) {
      throw new Error("Unable to load language file: " + filePath);
    }

    const data = await response.json();
    translationCache[lang] = data;
    return data;
  }

  function applyTranslations(dict) {
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) {
        el.textContent = dict[key];
      }
    });
  }

  async function setLanguage(lang) {
    let resolvedLang = lang;
    let dict;

    try {
      dict = await loadDictionary(resolvedLang);
    } catch (_) {
      resolvedLang = "en";
      dict = await loadDictionary("en");
    }

    document.documentElement.lang = resolvedLang;
    applyTranslations(dict);

    if (languageSelect) {
      languageSelect.value = resolvedLang;
    }
  }

  const languageSelect = document.getElementById("language-select");
  if (languageSelect) {
    languageSelect.addEventListener("change", function (event) {
      setLanguage(event.target.value);
    });
  }

  setLanguage("en");

  const form = document.getElementById("healthcoreForm");
  const successBanner = document.getElementById("formSuccess");

  const fields = {
    fullName: document.getElementById("fullName"),
    email: document.getElementById("email"),
    phone: document.getElementById("phone"),
    concerns: document.getElementById("concerns")
  };

  const errors = {
    fullName: document.getElementById("fullNameError"),
    email: document.getElementById("emailError"),
    phone: document.getElementById("phoneError"),
    concerns: document.getElementById("concernsError")
  };

  function showError(fieldKey, message) {
    const input = fields[fieldKey];
    const error = errors[fieldKey];
    error.textContent = message;
    error.classList.remove("hidden");
    input.setAttribute("aria-invalid", "true");
    input.classList.remove("border-slate-300");
    input.classList.add("border-red-500");
  }

  function clearError(fieldKey) {
    const input = fields[fieldKey];
    const error = errors[fieldKey];
    error.textContent = "";
    error.classList.add("hidden");
    input.setAttribute("aria-invalid", "false");
    input.classList.remove("border-red-500");
    input.classList.add("border-slate-300");
  }

  const validators = {
    fullName: function (value) {
      return value.length >= 3;
    },
    email: function (value) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    },
    phone: function (value) {
      return /^\+?[0-9\s()\-]{7,20}$/.test(value);
    },
    concerns: function (value) {
      return value.length >= 20;
    }
  };

  const validationMessages = {
    fullName: "Please enter your full name (at least 3 characters).",
    email: "Please enter a valid email address.",
    phone: "Please enter a valid phone number.",
    concerns: "Please provide at least 20 characters about your health concerns or other relevant information."
  };

  function validateField(fieldKey) {
    const value = fields[fieldKey].value.trim();
    if (!validators[fieldKey](value)) {
      showError(fieldKey, validationMessages[fieldKey]);
      return false;
    }
    clearError(fieldKey);
    return true;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    successBanner.classList.add("hidden");

    const allValid = Object.keys(fields).every(validateField);

    if (!allValid) {
      const firstInvalid = form.querySelector("[aria-invalid='true']");
      if (firstInvalid) {
        firstInvalid.focus();
      }
      return;
    }

    successBanner.classList.remove("hidden");
    form.reset();
  });

  Object.keys(fields).forEach(function (fieldKey) {
    fields[fieldKey].addEventListener("blur", function () {
      validateField(fieldKey);
    });
  });
})();
