export function init() {
  console.log('CoreAlpha UI placeholder ready');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  init();
}
