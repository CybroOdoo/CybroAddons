/** @odoo-module **/

function initOnlineApplication() {
    const container = document.getElementById('online_appl_form');
    if (!container) return;

    const courseSelect = container.querySelector('select[name="course"]');
    const deptSelect = container.querySelector('select[name="department"]');
    const semSelect = container.querySelector('select[name="semester"]');
    const form = container.querySelector('form');

    if (!courseSelect || !deptSelect || !semSelect) return;

    // Cache original options (including empty placeholder)
    const allDeptOptions = Array.from(deptSelect.querySelectorAll('option'));
    const allSemOptions = Array.from(semSelect.querySelectorAll('option'));

    function filterOptions() {
        const selectedCourse = courseSelect.value;
        const selectedDept = deptSelect.value;

        // Filter departments based on selected course
        deptSelect.innerHTML = '';
        allDeptOptions.forEach(opt => {
            if (!opt.value || !selectedCourse || opt.dataset.courseId === selectedCourse) {
                deptSelect.appendChild(opt.cloneNode(true));
            }
        });
        if (selectedDept && deptSelect.querySelector(`option[value="${selectedDept}"]`)) {
            deptSelect.value = selectedDept;
        } else {
            deptSelect.value = '';
        }

        // Filter semesters based on selected course and department
        const currentDept = deptSelect.value;
        semSelect.innerHTML = '';
        allSemOptions.forEach(opt => {
            const matchCourse = !selectedCourse || opt.dataset.courseId === selectedCourse;
            const matchDept = !currentDept || opt.dataset.departmentId === currentDept;
            if (!opt.value || (matchCourse && matchDept)) {
                semSelect.appendChild(opt.cloneNode(true));
            }
        });
    }

    courseSelect.addEventListener('change', () => {
        deptSelect.value = '';
        semSelect.value = '';
        filterOptions();
    });

    deptSelect.addEventListener('change', () => {
        semSelect.value = '';
        filterOptions();
    });

    if (form) {
        form.addEventListener('submit', (ev) => {
            const course = courseSelect.value;
            const department = deptSelect.value;
            const semester = semSelect.value;
            if (!course || !department || !semester) {
                ev.preventDefault();
                let errorBox = container.querySelector('.form-error-message');
                if (!errorBox) {
                    errorBox = document.createElement('div');
                    errorBox.className = 'form-error-message alert alert-danger mt-3';
                    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"], .btn_submit, #submit');
                    if (submitBtn) {
                        submitBtn.parentNode.insertBefore(errorBox, submitBtn);
                    } else {
                        form.appendChild(errorBox);
                    }
                }
                errorBox.textContent = 'Please select Course, Department, and Semester.';
                errorBox.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initOnlineApplication);
} else {
    initOnlineApplication();
}
