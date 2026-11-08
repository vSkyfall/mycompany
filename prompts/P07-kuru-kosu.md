# P7 · Kuru koşu — Claude çağırmadan akış

**Ne zaman:** Ajan dosyaları üretildikten sonra, ilk gerçek koşudan önce.

```
python3 bin/kos.py x-icerik --kuru koştur ve çıktıyı yorumla: ajana verilen istemin ilk satırı ne, hangi dosyaları hangi sırayla okuyacak, koşu kaydını nereye yazacak, bekçi ne zaman devreye girer.
```

> **Repoyu klonladıysan:** aynı komutu çalıştır — hiçbir şeye yazmaz, para harcamaz.
> İskeletin ayakta olduğunu görmenin en ucuz yolu budur.

**Beklenen çıktı:** `claude` hiç çağrılmaz, hiçbir dosyaya yazılmaz. Ekrana model, bütçe, araçlar,
yetenekler, koşu kaydının yazılacağı yol ve kurulan istem basılır. Çıktının en anlamlı satırı
kimlik satırıdır: ajanın koşuda göreceği ilk cümle.

**Dikkat:** Kuru koşu mesai kontrolünü ve anahtar kontrolünü de gösterir — eksik anahtar varsa
burada görürsün. Mesai dışında elle koşturmak için `--zorla` vardır.
