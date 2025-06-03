import json
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from openai import OpenAI
def load_video_data(file_path):
    """
    逐行读取 JSONL 格式的视频数据文件，
    每一行为一个视频的元数据，其中包含 keyframes 的 OCR 与 ASR 信息
    """
    video_data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                video_data.append(json.loads(line))
    return video_data

def build_index(video_data, embeddings):
    """
    遍历每个视频的 keyframe，拼接 OCR 和 ASR 文本，
    同时保存视频名称与时间戳作为元数据，构建向量索引
    """
    docs = []
    metadatas = []
    for video in video_data:
        video_name = video["video_name"]
        for keyframe in video.get("keyframes", []):
            ocr_text = " ".join(keyframe.get("ocr_result", []))
            asr_text = keyframe.get("asr_texts", "")
            content = f"屏幕内容：{ocr_text} 教师讲授： {asr_text}"
            docs.append(content)
            metadatas.append({
                "video_name": video_name,
                "time_point": keyframe["time_point"],
                "source": f"{video_name}@{keyframe['time_point']}"
            })
    # 使用传入的 embeddings 构建 FAISS 索引
    index = FAISS.from_texts(docs, embeddings, metadatas=metadatas)
    return index

def main():
    # 假设视频数据文件为 video_data.jsonl
    video_data = load_video_data("playground\keyframes_output\cc1147e9c64d5380a5f5ea9062513731-ld.json")
    
    # 设置硅基流动api的自定义 API 端点与 API Key
    silicon_api_base = "https://api.siliconflow.cn/v1"  # 示例端点
    api_key = "sk-ddoozzdqdeuxptrdxyhohdpkcjikxemkpxdcbhzlnfxahbts"  # 替换为实际的 API Key
    #client=OpenAI(base_url=silicon_api_base,api_key=api_key)
    # 初始化 LLM 与 Embeddings，均使用硅基流动api
    llm = ChatOpenAI(
        openai_api_key=api_key,
        openai_api_base=silicon_api_base,
        temperature=0.7,  # 根据需求调整参数
        model="deepseek-ai/DeepSeek-V3"
    )
    
    embeddings = OpenAIEmbeddings(
        #openai_api_base=silicon_api_base,
        openai_api_key=api_key,
        base_url=silicon_api_base,
        model='Pro/BAAI/bge-m3'
    )
    
    # 构建向量索引
    index = build_index(video_data, embeddings)
    
    # 初始化对话式检索问答系统（RAG + 多轮对话）
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=index.as_retriever(),return_source_documents=True)
    
    conversation_history = []
    print("输入 'quit' 退出。")
    while True:
        query = input("User: ")
        if query.strip().lower() == "quit":
            break
        # 调用链式问答系统，传入当前问题与对话历史
        result = qa_chain({"query": query, "chat_history": conversation_history})
        answer = result.get("answer", "")
        
        # 后处理：提取检索到的最相关文档信息，
        # 格式化返回 "video_name:time_point"，供前端跳转
        print(result)
        source_docs = result.get("sources", [])
        if source_docs:
            top_doc = source_docs[0]
            formatted_answer=top_doc
        else:
            formatted_answer = answer
        
        print("AI:", formatted_answer)
        conversation_history.append((query, answer))

if __name__ == "__main__":
    main()
