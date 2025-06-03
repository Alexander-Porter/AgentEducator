from funasr import AutoModel

model = AutoModel(model="paraformer-zh",disable_update=True)

res = model.generate(input="https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/test_audio/vad_example.wav")
print(res)