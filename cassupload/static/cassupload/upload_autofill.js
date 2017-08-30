$(document).ready(function () {
    $('input[type=file]').on('change', function () {
        if (!$('#id_name').val()) {
            var filename = $(this).val().split('\\').pop().split('/').pop().replace('.mp3', '');
            if (!/\s/g.test(filename)) // if no spaces
                $('#id_name').val(filename);
        }
    });
});
