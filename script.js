<script>
const doc = window.parent.document;
doc.addEventListener('keydown', function(e) {
    if (event.key == 'Enter' && e.ctrlKey) {
        buttons = Array.from(doc.querySelectorAll('button[kind=primary]'));
        const z_button = buttons.find(el => el.innerText === '文章生成');
        console.log(z_button)
        z_button.click();
        e.preventDefault()
    }
});
</script>
