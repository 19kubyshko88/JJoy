import g4f, asyncio

_providers = [
    g4f.Provider.Aichat,
    g4f.Provider.ChatBase,
    g4f.Provider.Bing,
    g4f.Provider.GptGo,
    g4f.Provider.You,
    g4f.Provider.Yqcloud,
]


async def run_provider(provider: g4f.Provider.BaseProvider, text):
    try :
        response = await g4f.ChatCompletion.create_async(model=g4f.models.default,
                                                         messages=[{"role": """user""",
                                                                    "content": f"Ты получишь транскрибацию аудио файла. Нужно переделать её в удобный для "
                                                                               f"чтения вид: поставить знаки препинания, исправить грамматику, прямую, "
                                                                               f"косвенную речь. Старайся как можно меньше изменять смысл текста. "
                                                                               f"СВОИ КОММЕНТАРИИИ НЕ ПИШИ!!! ОЦЕНОЧНЫХ СУЖДЕНИЙ НЕ ВЫСКАЗЫВАЙ!"
                                                                               f"Вот текст для исправления: {text}"}],
                                                         provider = provider,
                                                         )
        print(f"{provider.__name__}:", response)
    except Exception as e:
        print(f"{provider.__name__}:", e)


async def run_all(text):
    calls = [run_provider(provider) for provider in g4f.Provider.__all__]
    await asyncio.gather(*calls)



