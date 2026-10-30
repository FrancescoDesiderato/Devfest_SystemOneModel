from openai import OpenAI
client = OpenAI()

stream = client.responses.create(
  model="gpt-6-luna",
  service_tier="default",
  input=[
    {
      "role": "developer",
      "content": [
        {
          "type": "input_text",
          "text": "Help the user make a well-reasoned decision by comparing provided options based on key criteria. Be concise and objective."
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "I'm choosing between Billing and Tech Support . Which should I pick and why?"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "I was charged twice for my subscription this month. Could you help me get a refund for the extra charge?"
        }
      ]
    },
    {
      "type": "reasoning",
      "id": "rs_015c943271ba48ef006ae3b7f9440c87d288cb8df0a1053080",
      "summary": [
        {
          "type": "summary_text",
          "text": "**Clarifying billing support**\n\nI need to focus on answering questions related to billing and support, as I can’t actually process anything myself. It’s important to clarify whether the user needs to contact billing or support. Since the options are Billing vs Tech Support, I’ll select Billing as my focus. I'll remind the user to have their subscription account details, transaction dates, amounts, and receipts ready, but not to share payment info here. A concise message template could be helpful!"
        }
      ],
      "encrypted_content": "gAAAAABq47f6kdZnfPDZ7WdSUOoLZ-rhRdgqIncMTI4id_Okn2dyoZI5P_anvpgElNpb_ikaA2h0jNPK5Y0904LQPaCBTsW485yDqFiKdFTVEmokwbJhkzyTjAk7kukVuuRPyRAI5svUU1tCA9o4JYDBDUKIoesD6eU2V1T49HOv6voGoW7aU37DE8wsSsiDzt3id3DRtiNjszqHq7fBz2P5_KIysK6Wou2yrF-GOahs8ub3RfTABy7NdGzS4xkilfC8EgYkpn5W6rB6F0lWoEUH9TCRpKy2oI0RPQrwZBJZAgtiZH3jn5WqmJ3_lcRzTFQNjbfMrmAsIHCqHh6aZZhPg55g16mcswhQNhQbEehntApd4MMl6Cb_hrLVYIXxldXae8_xlFNi4YCTExtRxtLPcjt-Mcuuu95TYWdHbi5zmcLVHUDOg_N9vV2QHvcny09prPdoA8Qm36P62e7kQDMov0Q2ijINK_jkEi28Kjb9KR_RVcvlklICg-gAWCipz_dAieLQ35Gdj_4AVMjzYlP6Kf0y6D7H5wdCZGPMHuZ_XqXiWodfecsEEMnxrXFoHR1QzT-rH0YqenhzfSQNMm5XH6GfeKiT8tx9FeaJcXo80TJyBEGbxX571sZCXI2RsAtTsvjc8nWav8mfZSpnO_zM0epNybqAtZ1X06Gn6OMpHcSgbm608m40xwhnW-FAvcQuRZx3sHvUyVult9HFH9Wm5McutCBIoUWR3kq5Hd-Vrib-bAS31SrC1cwLUtdlrIbNev_0CnmEvnF7CjbfxI3M7kUILjat_lnyOyhmq_Yg8MKswdUm8F-Crs6JLKI0mZlxFDAL09PvOwxQIwoRJBBothAxPkUmwc9bfqCeSO6oF-A67nSFzimeOSa3APq3wRexsPc5opi4isQIBISAG47Vz9he_fRw36-W-_NwMrolqdd98pZR8WFVH8Qx3KsTNj7BbkvumrbyL3SvDDRsWHu4n5iWvfxdSIpyYNaxKIUUVjr-51QbKXR-xkKyJnESHfPgq4G7jfrdrMX9imIJX7YdbueCW_z1r48Z62yHb91hVOEjn4kgc6fAJEVXdVAMuwO-THszJraJaLMEVWmuCVFpzVDTsGZT4nCs5RvJ86MJpN3dhagOUVjmKMG6BUWZf5rm-kRlsEhGFSs2BwbMp6qt_FEKz3b3qgwp_Uh1JcZXP67aW91HHq70-Vsr9h8BzfKdMPL8ZoqB9m8h9axf06jEYCeG66JveNtnNrATf-ZdkMryYrRojX8Wfh4VrJib2YwQTuwMoxjrUF8HLqdpd4QVixiYG7U9hgrATaEZQ5qJGsliUhxb5CUY8msM1WL1bJj-hORp63nFfQSqtqs4-wRX8RW0bqeWOz3Hkr8a23nsJPdlgpkgF9S-Cu-JX-vWZIe8krVExrQxORQ_OVIJk6IIZwOHSjPhGG7Ldr9Pm_EBh6d7zInCHaBJ72PknLAMzdZ-jVdVvNq8E636X_xmuAiBJK9c9SoP3_0pa-pBRi-Fs5r-Pru8K-FPVLN4jT8NJyRzZbgjVb5MhbMW4lREdt1t3AbSbGWHfFI43x7M_9YkWyHVgz3tvhEA2RV8n4_nE8gyLlshoMhY9Xmet4ug1OKCRvNHBWOnArVc6SBIdfAgxWJOP2OspaHeBSdrSaKXx9qGDFrfkWvfD2ed8fyNqNNnl-vrcSb8-rRgAYw2pmwX9-IuY5Lpa0afz63S_-N-Y_LfPbir7L-wl_k3bk5WthtP2Pb4CvX4hMk2ZZHx1_TY0Ay7Sm4iKYolrWrwAUvmhGtNTx_vCqmOGDAQs0LfxSePN024WK74ZntCy3qZAEf3gmc8hUK-hbf6CJRd20S7Bc1tDgFcbet8-pMjynmrGU_CwFBLSJMMRtziPkays1HOdu6Xh7CnNUDvCBv1eq0RYzRFHucdsqIvzFOFNKlTzT7_DlTbl_lJ8MXpNC3GDtIwQUz8wd0Gmt4yfWDJ7gPp3o1-7Wn9bMMppaVg-R8gaYnk9aAooWb9yaWqkhramtu9P5JixTwjy5mJ8_A2DX_UW_XlLEZelhmbsmTnAevX9prPC8_NZrAyg9kMAtQ_zBXUqXS2rFZQCQh3hQoYEgFfzhh60FLWolzJn9neF7AEe2nG9D1yD9WxhEGukEDQNpSGsp_CsaVjOFZs0bc8UeB8JdavjLHhP2YcWkir3oW5zJOwCAdJ1rPYsHxwHU0aTTpxWSNpycq_CkUIvdkXwJ40AqVqQLBoF2P9P2s1MDO_tPUtJdI6eehn7NgLnj8JeiLQ9xYVwxJiupzZQxodwrreDYhz0lRrwMNl"
    },
    {
      "id": "msg_015c943271ba48ef006ae3b7fae93c87d2891da7b44275763c",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "Choose **Billing**—a duplicate subscription charge is a payment issue, not a technical one. Ask them to review the two charges and refund the extra one. Have the charge dates and amounts handy, but don’t share your full card number or password here."
        }
      ]
    }
  ],
  text={
    "format": {
      "type": "text"
    },
    "verbosity": "medium"
  },
  reasoning={
    "effort": "medium",
    "mode": "standard",
    "summary": "auto"
  },
  tools=[{ "type": "web_search_preview" }],
  stream=True,
  store=True,
  include=[
    "reasoning.encrypted_content",
    "web_search_call.action.sources"
  ]
)

for event in stream:
    print(event)