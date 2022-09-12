const form = document.getElementById('form');

form.addEventListener('submit', function handleSubmit(event) {
  event.preventDefault();

  // 👇️ Send data to server here
  form.submit()
  console.log(form)

  // 👇️ Reset form here
  form.reset();
});