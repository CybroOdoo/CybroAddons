/**
 * Hook to identify public holidays for calendar day cells.
 * Returns class names for FullCalendar's getDayCellClassNames hook.
 *
 * @param {Object} props
 * @returns {Function}
 */
export function usePublicHolidays(props) {
    return (info) => {
        const date = luxon.DateTime.fromJSDate(info.date).toISODate();
        const publicHoliday = props.model.publicHolidays?.[date];
        if (publicHoliday) {
            return ['fc-public-holiday'];
        }
        return [];
    };
}
