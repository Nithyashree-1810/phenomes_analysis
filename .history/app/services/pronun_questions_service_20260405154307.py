File "C:\Users\fidel\Desktop\phenomes_analysis\venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 1002, in run
    result = context.run(func, *args)
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\fidel\Desktop\phenomes_analysis\app\routes\question_route.py", line 18, in get_next_question
    questions = _service.generate_questions(score, num_questions=1)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\fidel\Desktop\phenomes_analysis\app\services\pronun_questions_service.py", line 41, in generate_questions
    prompt = _PROMPT_TEMPLATE.format(
             ^^^^^^^^^^^^^^^^^^^^^^^^
KeyError: '"difficulty"'