/** @odoo-module */
//Exports a custom hook usePublicHolidays that takes in props as a parameter.
//This hook is likely intended to be used in a calendar component to mark public holidays.
export function usePublicHolidays(props) {
    return (info) => {
        const date = luxon.DateTime.fromJSDate(info.date).toISODate();
        const publicHolidays = props.model.publicHolidays[date];
        if (publicHolidays) {
            info.el.classList.add('fc-public-holiday');
        }
    }
}
