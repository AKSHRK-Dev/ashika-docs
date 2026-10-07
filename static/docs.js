// Copy buttons on code blocks, the phone menu, and highlighting the current section in the table of contents.
document.querySelectorAll('.code .copy').forEach((button) => {
  button.addEventListener('click', async () => {
    const text = button.parentElement.querySelector('code').innerText;
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = 'コピーしました';
    } catch {
      button.textContent = 'コピーできません';
    }
    setTimeout(() => { button.textContent = 'コピー'; }, 1500);
  });
});

const menu = document.querySelector('.menu');
const side = document.getElementById('side');
if (menu && side) {
  const set = (open) => {
    side.classList.toggle('open', open);
    menu.setAttribute('aria-expanded', String(open));
    menu.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
  };
  menu.addEventListener('click', () => set(!side.classList.contains('open')));
  side.addEventListener('click', (event) => { if (event.target.closest('a')) set(false); });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') set(false); });
}

const tocLinks = [...document.querySelectorAll('.toc a')];
if (tocLinks.length && 'IntersectionObserver' in window) {
  const byId = new Map(tocLinks.map((a) => [a.getAttribute('href').slice(1), a]));
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      tocLinks.forEach((a) => a.classList.remove('on'));
      byId.get(entry.target.id)?.classList.add('on');
    });
  }, { rootMargin: '-70px 0px -70% 0px' });
  byId.forEach((_a, id) => { const el = document.getElementById(id); if (el) observer.observe(el); });
}
