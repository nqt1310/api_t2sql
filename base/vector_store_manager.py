import os
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import pandas as pd

class DataLoader:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def load_metadata_documents(self):
        df = self.df
        df.columns = [c.strip().upper() for c in df.columns]

        documents = []

        for table_name, g in df.groupby("TABLE_NAME"):
            lines = [f"Table: {table_name}"]
            for _, r in g.iterrows():
                lines.append(
                    f"- Column: {r['COLUMN_NAME']} | "
                    f"Type: {r['DATA_TYPE']} | "
                    f"Desc: {r['COLUMN_DESCRIPTION']}"
                )

            documents.append(
                Document(
                    page_content="\n".join(lines),
                    metadata={"table": table_name}
                )
            )

        return documents


class VectorStoreManager:
    def __init__(
        self,
        persist_dir: str,
        embedding,
        documents_loader,  # ← DataLoader
    ):
        self.persist_dir = persist_dir
        self.embedding = embedding
        self.documents_loader = documents_loader
        self.index_path = os.path.join(persist_dir, "index")

    def exists(self) -> bool:
        return os.path.exists(self.index_path)

    def build(self):
        print("🛠 Building FAISS index from metadata...")
        documents = self.documents_loader.load_metadata_documents()
        vectorstore = FAISS.from_documents(documents, self.embedding)
        vectorstore.save_local(self.persist_dir)
        return vectorstore

    def load(self):
        print("📦 Loading FAISS index...")
        return FAISS.load_local(
            self.persist_dir,
            self.embedding,
            allow_dangerous_deserialization=True,
        )

    def get_vectorstore(self):
        if not self.exists():
            return self.build()
        return self.load()

    def get_retriever(self, k: int = 5):
        vectorstore = self.get_vectorstore()
        return vectorstore.as_retriever(search_kwargs={"k": k})
