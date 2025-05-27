(function ($) {
    "use strict";

    document.addEventListener('DOMContentLoaded', () => {
        const testPaths = ['/test/', '/test_checkbox/', '/test_testo/', '/test_2nd/'];
        const currentPath = window.location.pathname;

        if (!testPaths.includes(currentPath)) {
            console.log("Non sei su una pagina test. Pulizia localStorage.");
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith('wrapped_') || key === 'customAnswer') {
                    localStorage.removeItem(key);
                }
            });
        } else {
            console.log("Sei su una pagina test, nessuna pulizia.");
        }
    });

    // === Preloader ===
    $(window).on('load', function () {
        $('[data-loader="circle-side"]').fadeOut();
        $('#preloader').delay(350).fadeOut('slow');
        $('body').delay(350).css({ 'overflow': 'visible' });


    });


    // === Logica per ogni form ===
    document.querySelectorAll('form.step-form').forEach(form => {
        const formId = form.getAttribute('id');
        const storedData = JSON.parse(localStorage.getItem(formId) || '{}');

        // Ripristina risposte
        Object.keys(storedData).forEach(name => {
            const value = storedData[name];
            const inputs = form.querySelectorAll(`[name="${name}"]`);
            inputs.forEach(input => {
                if (input.type === 'checkbox' || input.type === 'radio') {
                    input.checked = value.includes(input.value);
                } else {
                    input.value = value;
                }
            });
        });

        // === Se formId è wrapped_2, gestisci il customAnswer ===
        if (formId === 'wrapped_2') {
            const radioButtons = form.querySelectorAll('input[name="question_2[]"]');
            const customWrapper = form.querySelector('#custom-answer-wrapper');
            const customTextarea = form.querySelector('#customAnswer');

            if (radioButtons.length && customWrapper && customTextarea) {
                // Mostra solo se "Sì" è selezionato (valore "5")
                const selected = Array.from(radioButtons).find(r => r.checked);
                if (selected && selected.value == "5") {
                    customWrapper.style.display = 'block';
                } else {
                    customWrapper.style.display = 'none';
                }

                // Listener per mostrare/nascondere in base al cambio
                radioButtons.forEach(radio => {
                    radio.addEventListener('change', () => {
                        if (radio.value == "5") {
                            customWrapper.style.display = 'block';
                        } else {
                            customWrapper.style.display = 'none';
                            customTextarea.value = '';
                            const currentData = JSON.parse(localStorage.getItem(formId) || '{}');
                            delete currentData['customAnswer'];
                            localStorage.setItem(formId, JSON.stringify(currentData));
                        }
                    });
                });

                // Ripristina da localStorage
                if (storedData['customAnswer']) {
                    customTextarea.value = storedData['customAnswer'];
                }

                customTextarea.addEventListener('input', () => {
                    const currentData = JSON.parse(localStorage.getItem(formId) || '{}');
                    currentData['customAnswer'] = customTextarea.value.trim();
                    localStorage.setItem(formId, JSON.stringify(currentData));
                });
            }
        }
        const prev = document.getElementById('prev-button');

        // Rimuovi l'attributo required dagli input quando si clicca il prev-button
        if (prev) {
            prev.addEventListener('click', function (e) {
            e.preventDefault(); // Previene l'invio immediato del form
            // Rimuove required da tutti gli input nel form corrente
            form.querySelectorAll('[required]').forEach(function (input) {
                input.removeAttribute('required');
            });
            // Aggiungi input nascosto per simulare il valore del bottone
            let hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'action';
            hidden.value = 'prev';
            form.appendChild(hidden);

            // Invia manualmente il form
            form.submit();
            });
        }

        // === Validazione ===
        form.addEventListener('submit', function (e) {
            // Controlla quale pulsante è stato premuto tra "next" o "prev"
            const action = e.submitter ? e.submitter.value : ''; 
            
            // Se l'azione è "prev", non fa la validazione
            if (action === 'prev') {
                return; 
            }

            // Se l'azione è "next", procedi con la validazione
            form.querySelectorAll('.error').forEach(el => el.remove()); // Rimuovi gli errori esistenti
            let formValid = true;
            const formData = {};

            const allFields = Array.from(form.querySelectorAll('input[name], select[name], textarea[name]'));
            const fieldGroups = [...new Set(allFields.map(el => el.name))];
            
            fieldGroups.forEach(name => {
                const fields = form.querySelectorAll(`[name="${name}"]`);
                const type = fields[0].type;
                const isCheckbox = type === 'checkbox';
                const isRadio = type === 'radio';
                const isRequired = fields[0].hasAttribute('required') || isCheckbox || isRadio;

                if (!isRequired) return;

                let isValid = false;
                let value = [];

                if (isCheckbox || isRadio) {
                    fields.forEach(el => {
                        if (el.checked) value.push(el.value);
                    });
                    isValid = value.length > 0;
                } else {
                    value = fields[0].value.trim();
                    isValid = value !== '';
                }

                formData[name] = value;

                if (!isValid) {
                    formValid = false;
                    const formGroup = fields[0].closest('.container_check') || fields[0].closest('.form-group') || fields[0].parentElement;
                    const errorSpan = document.createElement('span');
                    errorSpan.classList.add('error');
                    errorSpan.innerText = 'Campo obbligatorio';
                    if (!formGroup.querySelector('.error')) {
                        formGroup.appendChild(errorSpan);
                    }
                }
            });



            // 👇 Salva customAnswer manualmente se c'è
            const customTextarea = form.querySelector('#customAnswer');
            if (customTextarea) {
                formData['customAnswer'] = customTextarea.value.trim();
            }

            if (!formValid) {
                e.preventDefault(); // Prevenire l'invio del form se non valido
                const firstError = form.querySelector('.error');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            } else {
                localStorage.setItem(formId, JSON.stringify(formData)); // Salva i dati nel localStorage
            }
        });

        // === Errori dinamici ===
        form.querySelectorAll('input, select, textarea').forEach(el => {
            el.addEventListener('input', () => clearError(el));
            el.addEventListener('change', () => clearError(el));
        });

        function clearError(el) {
            const group = el.closest('.container_check') || el.closest('.form-group') || el.parentElement;
            const error = group.querySelector('.error');
            if (error) error.remove();
        }

        // === Tasto Indietro ===
        const prevButton = form.querySelector('button[name="backward"]');
        if (prevButton && prevButton.dataset.prevUrl) {
            prevButton.classList.remove('d-none');
            prevButton.addEventListener('click', function () {
                window.location.href = prevButton.dataset.prevUrl; // Gestisci il tasto indietro
            });
        }

    });

    

})(window.jQuery);
