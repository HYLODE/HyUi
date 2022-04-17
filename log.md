# Running notes log

## 2022-04-17t15:14:57
seleniumbase as an alternative 
https://blog.streamlit.io/testing-streamlit-apps-using-seleniumbase/
some nice conceptual notes on testing
> ## Defining Test Success
> There are several ways to think about what constitutes looking the same in terms of testing. I chose the following three principles for testing my streamlit-folium package:
> 1. The Document Object Model (DOM) structure (but not necessarily the values) of the page should remain the same
> 2. For values such as headings, test that those values are exactly equal
> 3. Visually, the app should look the same  
> 
> I decided to take these less strict definitions of “unchanged” for testing streamlit-folium, as the internals of the Folium package itself appear to be non-deterministic. Meaning, the same Python code will create the same looking image, but the generated HTML will be different.

```shell
pip3 install seleniumbase
sbase
```

BUT ... https://github.com/seleniumbase/SeleniumBase/issues/1069#issuecomment-1100893208
does not seem compatible
 
## 2022-04-17t11:28:29
- fresh set-up of project
- 
