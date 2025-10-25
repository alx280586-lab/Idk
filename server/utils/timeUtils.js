export function minutesAgo(referenceDate, minutes) {
  const result = new Date(referenceDate);
  result.setMinutes(result.getMinutes() - minutes);
  return result;
}
